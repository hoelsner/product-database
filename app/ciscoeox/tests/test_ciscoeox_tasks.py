"""
Test suite for the ciscoeox.tasks module
"""
import datetime
import pytest
import json
import requests
from mixer.backend.django import mixer
from requests import Response
from app.ciscoeox import tasks
from app.ciscoeox.exception import CiscoApiCallFailed, CredentialsNotFoundException
from app.config import utils
from app.config.models import NotificationMessage
from app.config.settings import AppSettings
from app.productdb.models import Product, Vendor
import app.ciscoeox.api_crawler as cisco_eox_api_crawler
from django_project.celery import TaskState

pytestmark = pytest.mark.django_db

CREDENTIALS_FILE = ".cisco_api_credentials"


@pytest.fixture
def use_test_api_configuration():
    app = AppSettings()
    with open(CREDENTIALS_FILE) as f:
        content = json.loads(f.read())
    app.set_cisco_api_enabled(True)
    app.set_product_blacklist_regex("")
    app.set_cisco_eox_api_queries("")
    app.set_auto_create_new_products(True)
    app.set_periodic_sync_enabled(False)
    app.set_cisco_api_client_id(content.get("client_id", "dummy_id"))
    app.set_cisco_api_client_id(content.get("client_secret", "dummy_secret"))


@pytest.mark.usefixtures("mock_cisco_api_authentication_server")
@pytest.mark.usefixtures("use_test_api_configuration")
@pytest.mark.usefixtures("set_celery_always_eager")
@pytest.mark.usefixtures("redis_server_required")
@pytest.mark.usefixtures("import_default_vendors")
class TestExecuteTaskToSynchronizeCiscoEoxStateTask:
    def mock_api_call(self, monkeypatch):
        # mock the underlying API call
        class MockSession:
            def get(self, *args, **kwargs):
                r = Response()
                r.status_code = 200
                with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_1.json") as f:
                    r._content = f.read().encode("utf-8")
                return r

        monkeypatch.setattr(requests, "Session", MockSession)

    def test_manual_task(self, monkeypatch):
        self.mock_api_call(monkeypatch)

        # try to execute it, while no auto-sync is enabled
        app = AppSettings()
        app.set_periodic_sync_enabled(False)
        app.set_cisco_eox_api_queries("WS-C2960-*")

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay(ignore_periodic_sync_flag=True)
        expected_result = '<p style="text-align: left;">The following queries were executed:<br>' \
                          '<ul style="text-align: left;"><li><code>WS-C2960-*</code> (<b>affects 3 products</b>, ' \
                          'success)</li></ul></p>'

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == expected_result
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"
        assert Product.objects.count() == 3, "Three products are part of the update"

        # test update required
        p = Product.objects.get(product_id="WS-C2950G-24-EI")
        p.eox_update_time_stamp = datetime.date(1999, 1, 1)
        p.save()

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay(ignore_periodic_sync_flag=True)
        expected_result = '<p style="text-align: left;">The following queries were executed:<br>' \
                          '<ul style="text-align: left;"><li><code>WS-C2960-*</code> (<b>affects 3 products</b>, ' \
                          'success)</li></ul></p>'

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == expected_result
        assert NotificationMessage.objects.count() == 2, "Task should create a Notification Message"
        assert Product.objects.count() == 3, "Three products are part of the update"

    def test_manual_task_with_single_blacklist_entry(self, monkeypatch):
        self.mock_api_call(monkeypatch)

        # try to execute it, while no auto-sync is enabled
        app = AppSettings()
        app.set_periodic_sync_enabled(False)
        app.set_cisco_eox_api_queries("WS-C2960-*")
        app.set_product_blacklist_regex("WS-C2950G-24-EI")

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay(ignore_periodic_sync_flag=True)
        expected_result = '<p style="text-align: left;">The following queries were executed:<br>' \
                          '<ul style="text-align: left;"><li><code>WS-C2960-*</code> (<b>affects 3 products</b>, ' \
                          'success)</li></ul>' \
                          '<br>The following comment/errors occurred during the synchronization:<br>' \
                          '<ul style="text-align: left;">' \
                          '<li><code>WS-C2950G-24-EI</code>:  Product record ignored</li></ul></p>'

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == expected_result
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"
        assert Product.objects.count() == 2
        nm = NotificationMessage.objects.first()
        assert nm.type == NotificationMessage.MESSAGE_SUCCESS, "Incomplete configuration, should throw a warning "

    def test_manual_task_with_multiple_blacklist_entries(self, monkeypatch):
        self.mock_api_call(monkeypatch)

        # try to execute it, while no auto-sync is enabled
        app = AppSettings()
        app.set_periodic_sync_enabled(False)
        app.set_cisco_eox_api_queries("WS-C2960-*")
        app.set_product_blacklist_regex("WS-C2950G-48-EI-WS;WS-C2950G-24-EI")

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay(ignore_periodic_sync_flag=True)
        expected_result = [
            '<p style="text-align: left;">The following queries were executed:<br>'
            '<ul style="text-align: left;"><li><code>WS-C2960-*</code> (<b>affects 3 products</b>, '
            'success)</li></ul>',
            '<br>The following comment/errors occurred during the synchronization:'
            '<br><ul style="text-align: left;">',
            '<li><code>WS-C2950G-24-EI</code>:  Product record ignored</li>',
            '<li><code>WS-C2950G-48-EI-WS</code>:  Product record ignored</li>'
        ]

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        for er in expected_result:
            assert er in task.info.get("status_message")
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"
        assert Product.objects.count() == 1, "Only a single product is imported"
        nm = NotificationMessage.objects.first()
        assert nm.type == NotificationMessage.MESSAGE_SUCCESS, "Incomplete configuration, should throw a warning "

    def test_periodic_task_without_queries(self, monkeypatch):
        self.mock_api_call(monkeypatch)

        # test automatic trigger
        app = AppSettings()
        app.set_periodic_sync_enabled(True)
        app.set_cisco_eox_api_queries("")

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay()

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == "No Cisco EoX API queries configured."
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"
        nm = NotificationMessage.objects.first()
        assert nm.type == NotificationMessage.MESSAGE_WARNING, "Incomplete configuration, should throw a warning " \
                                                               "message"

    def test_api_call_error(self, monkeypatch):
        # force API failure
        class MockSession:
            def get(self, *args, **kwargs):
                raise CiscoApiCallFailed("The API is broken")

        monkeypatch.setattr(requests, "Session", MockSession)

        # test automatic trigger
        app = AppSettings()
        app.set_periodic_sync_enabled(True)
        app.set_cisco_eox_api_queries("yxcz")

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay()

        expected_status_message = '<p style="text-align: left;">The following queries were executed:<br>' \
                                  '<ul style="text-align: left;">' \
                                  '<li class="text-danger"><code>yxcz</code> (failed, cannot contact API endpoint ' \
                                  'at https://api.cisco.com/supporttools/eox/rest/5/EOXByProductID/1/yxcz)</li>' \
                                  '</ul></p>'

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == expected_status_message
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"
        nm = NotificationMessage.objects.first()
        assert nm.type == NotificationMessage.MESSAGE_ERROR, "Should be an error message, because all queries failed"

    def test_credentials_not_found(self, monkeypatch):
        # force API failure
        class MockSession:
            def get(self, *args, **kwargs):
                raise CredentialsNotFoundException("Something is wrong with the credentials handling")

        monkeypatch.setattr(requests, "Session", MockSession)

        # test automatic trigger
        app = AppSettings()
        app.set_periodic_sync_enabled(True)
        app.set_cisco_eox_api_queries("yxcz")

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay()

        expected_status_message = '<p style="text-align: left;">The following queries were executed:<br>' \
                                  '<ul style="text-align: left;"><li class="text-danger"><code>yxcz</code> ' \
                                  '(failed, cannot contact API endpoint at ' \
                                  'https://api.cisco.com/supporttools/eox/rest/5/EOXByProductID/1/yxcz)</li></ul></p>'

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == expected_status_message
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"
        nm = NotificationMessage.objects.first()
        assert nm.type == NotificationMessage.MESSAGE_ERROR, "Should be an error message, because all queries failed"

    def test_api_check_failed(self, monkeypatch):
        # force API failure
        class MockSession:
            def get(self, *args, **kwargs):
                raise Exception("The API is broken")

        monkeypatch.setattr(requests, "Session", MockSession)

        # test automatic trigger
        app = AppSettings()
        app.set_periodic_sync_enabled(True)
        app.set_cisco_eox_api_queries("yxcz")

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay()

        expected_status_message = "<p style=\"text-align: left;\">The following queries were executed:<br>" \
                                  "<ul style=\"text-align: left;\"><li class=\"text-danger\"><code>yxcz</code> " \
                                  "(failed, cannot contact API endpoint at " \
                                  "https://api.cisco.com/supporttools/eox/rest/5/EOXByProductID/1/yxcz)</li></ul></p>"

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == expected_status_message
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"
        nm = NotificationMessage.objects.first()
        assert nm.type == NotificationMessage.MESSAGE_ERROR, "Should be an error message, because all queries failed"

    def test_periodic_task_enabled_state(self, monkeypatch):
        self.mock_api_call(monkeypatch)

        # test automatic trigger
        app = AppSettings()
        app.set_periodic_sync_enabled(False)
        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay()

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == "task not enabled"

        app.set_periodic_sync_enabled(True)

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay()

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") != "task not enabled"

    def test_execute_task_to_synchronize_cisco_eox_states_with_failed_api_query(self, monkeypatch):
        def raise_ciscoapicallfailed():
            raise CiscoApiCallFailed("Cisco API call failed message")

        monkeypatch.setattr(utils, "check_cisco_eox_api_access", lambda x, y, z: True)
        monkeypatch.setattr(
            cisco_eox_api_crawler,
            "get_raw_api_data",
            lambda api_query=None, year=None: raise_ciscoapicallfailed()
        )

        # test automatic trigger
        app = AppSettings()
        app.set_periodic_sync_enabled(True)
        app.set_cisco_eox_api_queries("yxcz")

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay()

        expected_status_message = "<p style=\"text-align: left;\">The following queries were executed:<br>" \
                                  "<ul style=\"text-align: left;\"><li class=\"text-danger\">" \
                                  "<code>yxcz</code> (failed, Cisco API call failed message)</li></ul></p>"

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == expected_status_message
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"
        nm = NotificationMessage.objects.first()
        assert nm.type == NotificationMessage.MESSAGE_ERROR, "Should be an error message, because all queries failed"


@pytest.mark.usefixtures("set_celery_always_eager")
@pytest.mark.usefixtures("redis_server_required")
class TestPopulateProductLifecycleStateSyncTask:
    def test_no_cisco_vendor(self):
        result = tasks.cisco_eox_populate_product_lc_state_sync_field.delay()

        assert result.status == "SUCCESS"
        assert result.info == {"error": "Vendor \"Cisco Systems\" not found in database"}

    @pytest.mark.usefixtures("import_default_vendors")
    def test_no_cisco_products(self):
        result = tasks.cisco_eox_populate_product_lc_state_sync_field.delay()

        assert result.status == "SUCCESS"
        assert result.info == {"error": "No Products associated to \"Cisco Systems\" found in database"}

    @pytest.mark.usefixtures("import_default_vendors")
    def test_populate_flag_on_cisco_products(self):
        app_config = AppSettings()
        v = Vendor.objects.get(id=1)
        mixer.blend("productdb.Product", product_id="est", vendor=v, lc_state_sync=False)
        mixer.blend("productdb.Product", product_id="Test", vendor=v, lc_state_sync=False)
        mixer.blend("productdb.Product", product_id="TestA", vendor=v, lc_state_sync=False)
        mixer.blend("productdb.Product", product_id="TestB", vendor=v, lc_state_sync=False)
        mixer.blend("productdb.Product", product_id="TestC", vendor=v, lc_state_sync=False)
        mixer.blend("productdb.Product", product_id="ControlItem", vendor=v, lc_state_sync=False)

        # the following item is part of every query, but is never synced because of the wrong vendor
        mixer.blend("productdb.Product", product_id="Other ControlItem", lc_state_sync=False)

        app_config.set_cisco_eox_api_queries("")
        app_config.set_periodic_sync_enabled(True)

        result = tasks.cisco_eox_populate_product_lc_state_sync_field.delay()

        assert result.status == "SUCCESS"
        assert Product.objects.filter(lc_state_sync=True).count() == 0, "No queries configured"

        app_config.set_cisco_eox_api_queries("Test\nOther ControlItem")

        result = tasks.cisco_eox_populate_product_lc_state_sync_field.delay()
        filterquery = Product.objects.filter(lc_state_sync=True)

        assert result.status == "SUCCESS"
        assert list(filterquery.order_by("id").values_list("product_id", flat=True)) == ["Test"]

        app_config.set_cisco_eox_api_queries("Test*\nOther ControlItem")

        result = tasks.cisco_eox_populate_product_lc_state_sync_field.delay()
        filterquery = Product.objects.filter(lc_state_sync=True)
        expected_result_list = [
            "Test",
            "TestA",
            "TestB",
            "TestC",
        ]

        assert result.status == "SUCCESS"
        assert list(filterquery.order_by("id").values_list("product_id", flat=True)) == expected_result_list

        app_config.set_cisco_eox_api_queries("*estB\nOther ControlItem")

        result = tasks.cisco_eox_populate_product_lc_state_sync_field.delay()
        filterquery = Product.objects.filter(lc_state_sync=True)
        expected_result_list = [
            "TestB",
        ]

        assert result.status == "SUCCESS"
        assert list(filterquery.order_by("id").values_list("product_id", flat=True)) == expected_result_list

        app_config.set_cisco_eox_api_queries("*estB\nOther ControlItem")

        result = tasks.cisco_eox_populate_product_lc_state_sync_field.delay()
        filterquery = Product.objects.filter(lc_state_sync=True)
        expected_result_list = [
            "TestB",
        ]

        assert result.status == "SUCCESS"
        assert list(filterquery.order_by("id").values_list("product_id", flat=True)) == expected_result_list

        app_config.set_cisco_eox_api_queries("*es*\nOther ControlItem")

        result = tasks.cisco_eox_populate_product_lc_state_sync_field.delay()
        filterquery = Product.objects.filter(lc_state_sync=True)
        expected_result_list = [
            "est",
            "Test",
            "TestA",
            "TestB",
            "TestC",
        ]

        assert result.status == "SUCCESS"
        assert list(filterquery.order_by("id").values_list("product_id", flat=True)) == expected_result_list

        app_config.set_cisco_eox_api_queries("*es*\nOther ControlItem")
        app_config.set_periodic_sync_enabled(False)

        result = tasks.cisco_eox_populate_product_lc_state_sync_field.delay()
        filterquery = Product.objects.filter(lc_state_sync=True)

        assert result.status == "SUCCESS"
        assert filterquery.count() == 0, "Periodic sync disabled, no value should be true"


@pytest.mark.usefixtures("mock_cisco_api_authentication_server")
@pytest.mark.usefixtures("use_test_api_configuration")
@pytest.mark.usefixtures("set_celery_always_eager")
@pytest.mark.usefixtures("redis_server_required")
@pytest.mark.usefixtures("import_default_vendors")
class TestInitialSyncWithCiscoEoXApiTask:
    def mock_api_call(self, monkeypatch):
        # mock the underlying API call
        class MockSession:
            def get(self, *args, **kwargs):
                r = Response()
                r.status_code = 200
                with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_1.json") as f:
                    r._content = f.read().encode("utf-8")
                return r

        monkeypatch.setattr(requests, "Session", MockSession)

    def test_initial_import_with_invalid_parameters(self):
        with pytest.raises(AttributeError) as ex:
            tasks.initial_sync_with_cisco_eox_api.delay(years_list="invalid parameter")

        assert ex.match("years_list must be a list")

        with pytest.raises(AttributeError) as ex:
            tasks.initial_sync_with_cisco_eox_api.delay(years_list=["12", "13"])

        assert ex.match("years_list must be a list of integers")

        task = tasks.initial_sync_with_cisco_eox_api.delay(years_list=[])

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == "No years provided, nothing to do."

    def test_initial_import(self, monkeypatch):
        self.mock_api_call(monkeypatch)

        # start initial import
        task = tasks.initial_sync_with_cisco_eox_api.delay(years_list=[2018, 2017])
        expected_result = "The EoX data were successfully downloaded for the following years: 2018,2017"

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == expected_result
        assert Product.objects.count() == 3, "Three products are part of the update (mocked)"
        assert NotificationMessage.objects.filter(title="Initial data import finished").count() == 1

    def test_initial_import_with_failed_api_query(self, monkeypatch):
        def raise_ciscoapicallfailed():
            raise CiscoApiCallFailed("Cisco API call failed message")

        monkeypatch.setattr(utils, "check_cisco_eox_api_access", lambda x, y, z: True)
        monkeypatch.setattr(
            cisco_eox_api_crawler,
            "get_raw_api_data",
            lambda api_query=None, year=None: raise_ciscoapicallfailed()
        )

        # test initial import
        task = tasks.initial_sync_with_cisco_eox_api.delay(years_list=[2018, 2017])

        expected_status_message = "The EoX data were successfully downloaded for the following years: None " \
                                  "(for 2018,2017 the synchronization failed)"

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == expected_status_message
        msg_count = NotificationMessage.objects.filter(title="Initial data import failed").count()
        assert msg_count == 2, "Message is created per year"
