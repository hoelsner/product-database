"""
Test suite for the ciscoeox.tasks module
"""
import datetime
import pytest
import json
import requests
from requests import Response
from app.ciscoeox import api_crawler
from app.ciscoeox import tasks
from app.ciscoeox.exception import CiscoApiCallFailed, CredentialsNotFoundException
from app.config.models import NotificationMessage
from app.productdb.models import Product
from django_project.celery import TaskState

pytestmark = pytest.mark.django_db

CISCO_API_ENABLED = True
PRODUCT_BLACKLIST_REGEX = ""
CISCO_EOX_API_QUERIES = ""
AUTO_CREATE_NEW_PRODUCTS = True
CISCO_EOX_API_AUTO_SYNC_ENABLED = False


class BaseCiscoApiConsoleSettings:
    """
    Mock object that provides the Cisco API credentials used for online tests. If no credentials are found, dummy
    values are used. The source file for the Test API credentials are read from the ".cisco_api_credentials" file,
    which should have the following format:

    {
        "id": "",
        "secret": ""
    }

    """
    CREDENTIALS_FILE = ".cisco_api_credentials"

    def read_file(self):
        pass

    def load_client_credentials(self):
        pass

    def is_cisco_api_enabled(self):
        return CISCO_API_ENABLED

    def get_product_blacklist_regex(self):
        return PRODUCT_BLACKLIST_REGEX

    def is_auto_create_new_products(self):
        return AUTO_CREATE_NEW_PRODUCTS

    def get_cisco_eox_api_queries(self):
        return CISCO_EOX_API_QUERIES

    def is_cisco_eox_api_auto_sync_enabled(self):
        return CISCO_EOX_API_AUTO_SYNC_ENABLED

    def get_cisco_api_client_id(self):
        try:
            with open(self.CREDENTIALS_FILE) as f:
                return json.loads(f.read())["client_id"]
        except:
            return "dummy_id"

    def get_cisco_api_client_secret(self):
        try:
            with open(self.CREDENTIALS_FILE) as f:
                return json.loads(f.read())["client_secret"]
        except:
            return "dummy_secret"


@pytest.fixture
def use_test_api_configuration(monkeypatch):
    monkeypatch.setattr(tasks, "AppSettings", BaseCiscoApiConsoleSettings)
    monkeypatch.setattr(api_crawler, "AppSettings", BaseCiscoApiConsoleSettings)


@pytest.mark.usefixtures("use_test_api_configuration")
@pytest.mark.usefixtures("set_celery_always_eager")
@pytest.mark.usefixtures("redis_server_required")
@pytest.mark.usefixtures("import_default_vendors")
class TestExecuteTaskToSynchronizeCiscoEoxStateTask:
    def mock_api_call(sel, monkeypatch):
        # mock the underlying API call
        def mock_response():
            r = Response()
            r.status_code = 200
            with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_1.json") as f:
                r._content = f.read().encode("utf-8")
            return r

        monkeypatch.setattr(requests, "get", lambda x, headers: mock_response())

    def test_manual_task(self, monkeypatch):
        self.mock_api_call(monkeypatch)

        # try to execute it, while no auto-sync is enabled
        global CISCO_API_ENABLED
        global CISCO_EOX_API_AUTO_SYNC_ENABLED
        global CISCO_EOX_API_QUERIES
        CISCO_API_ENABLED = True
        CISCO_EOX_API_AUTO_SYNC_ENABLED = False
        CISCO_EOX_API_QUERIES = "WS-C2960-*"

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay(ignore_periodic_sync_flag=True)
        expected_result = '<div style="text-align:left;"><h3>Query: WS-C2960-*</h3>The following products are ' \
                          'affected by this update:</p><ul><li>create the Product <code>WS-C2950G-48-EI-WS</code> ' \
                          'in the database</li><li>create the Product <code>WS-C2950T-48-SI-WS</code> in the ' \
                          'database</li><li>create the Product <code>WS-C2950G-24-EI</code> in the database</li>' \
                          '</ul></div>'

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == expected_result
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"
        assert Product.objects.count() == 3, "Three products are part of the update"

        # test no changes required
        CISCO_API_ENABLED = True
        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay(ignore_periodic_sync_flag=True)
        expected_result = '<div style="text-align:left;"><h3>Query: WS-C2960-*</h3>No changes required.</div>'

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == expected_result
        assert NotificationMessage.objects.count() == 2, "Task should create a Notification Message"
        assert Product.objects.count() == 3, "Three products are part of the update"

        # test update required
        p = Product.objects.get(product_id="WS-C2950G-24-EI")
        p.eox_update_time_stamp = datetime.date(1999, 1, 1)
        p.save()

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay(ignore_periodic_sync_flag=True)
        expected_result = '<div style="text-align:left;"><h3>Query: WS-C2960-*</h3>The following products are ' \
                          'affected by this update:</p><ul><li>update the Product data for <code>WS-C2950G-24-EI' \
                          '</code></li></ul></div>'

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == expected_result
        assert NotificationMessage.objects.count() == 3, "Task should create a Notification Message"
        assert Product.objects.count() == 3, "Three products are part of the update"

    def test_manual_task_with_single_blacklist_entry(self, monkeypatch):
        self.mock_api_call(monkeypatch)

        # try to execute it, while no auto-sync is enabled
        global CISCO_API_ENABLED
        global CISCO_EOX_API_AUTO_SYNC_ENABLED
        global PRODUCT_BLACKLIST_REGEX
        global CISCO_EOX_API_QUERIES
        CISCO_API_ENABLED = True
        CISCO_EOX_API_AUTO_SYNC_ENABLED = False
        PRODUCT_BLACKLIST_REGEX = "WS-C2950G-24-EI"
        CISCO_EOX_API_QUERIES = "WS-C2960-*"

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay(ignore_periodic_sync_flag=True)
        expected_result = '<div style="text-align:left;"><h3>Query: WS-C2960-*</h3>The following products are ' \
                          'affected by this update:</p><ul><li>create the Product <code>WS-C2950G-48-EI-WS</code> ' \
                          'in the database</li><li>create the Product <code>WS-C2950T-48-SI-WS</code> in the ' \
                          'database</li><li>Product data for <code>WS-C2950G-24-EI</code> ignored</li>' \
                          '</ul></div>'

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == expected_result
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"
        assert Product.objects.count() == 2

    def test_manual_task_with_multiple_blacklist_entries(self, monkeypatch):
        self.mock_api_call(monkeypatch)

        # try to execute it, while no auto-sync is enabled
        global CISCO_API_ENABLED
        global CISCO_EOX_API_AUTO_SYNC_ENABLED
        global PRODUCT_BLACKLIST_REGEX
        global CISCO_EOX_API_QUERIES
        CISCO_API_ENABLED = True
        CISCO_EOX_API_AUTO_SYNC_ENABLED = False
        PRODUCT_BLACKLIST_REGEX = "WS-C2950G-48-EI-WS;WS-C2950G-24-EI"
        CISCO_EOX_API_QUERIES = "WS-C2960-*"

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay(ignore_periodic_sync_flag=True)
        expected_result = '<div style="text-align:left;"><h3>Query: WS-C2960-*</h3>The following products are ' \
                          'affected by this update:</p><ul><li>Product data for <code>WS-C2950G-48-EI-WS</code> ' \
                          'ignored</li><li>create the Product <code>WS-C2950T-48-SI-WS</code> in the ' \
                          'database</li><li>Product data for <code>WS-C2950G-24-EI</code> ignored</li>' \
                          '</ul></div>'

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == expected_result
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"
        assert Product.objects.count() == 1, "Only a single product is imported"

    def test_periodic_task_without_queries(self, monkeypatch):
        self.mock_api_call(monkeypatch)

        # test automatic trigger
        global CISCO_API_ENABLED
        global CISCO_EOX_API_AUTO_SYNC_ENABLED
        global CISCO_EOX_API_QUERIES
        CISCO_API_ENABLED = True
        CISCO_EOX_API_AUTO_SYNC_ENABLED = True
        CISCO_EOX_API_QUERIES = ""

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay()

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == "No Cisco EoX API queries configured."
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"

    def test_api_call_error(self, monkeypatch):
        # force API failure
        def mock_response():
            raise CiscoApiCallFailed("The API is broken")

        monkeypatch.setattr(api_crawler, "update_cisco_eox_database", lambda query: mock_response())

        # test automatic trigger
        global CISCO_API_ENABLED
        global CISCO_EOX_API_AUTO_SYNC_ENABLED
        global CISCO_EOX_API_QUERIES
        CISCO_API_ENABLED = True
        CISCO_EOX_API_AUTO_SYNC_ENABLED = True
        CISCO_EOX_API_QUERIES = "yxcz"

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay()

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message", None) is None
        assert task.info.get("error_message") == "Cisco EoX API call failed (The API is broken)"
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"

    def test_credentials_not_found(self, monkeypatch):
        # force API failure
        def mock_response():
            raise CredentialsNotFoundException("Something is wrong with the credentials handling")

        monkeypatch.setattr(api_crawler, "update_cisco_eox_database", lambda query: mock_response())

        # test automatic trigger
        global CISCO_API_ENABLED
        global CISCO_EOX_API_AUTO_SYNC_ENABLED
        global CISCO_EOX_API_QUERIES
        CISCO_API_ENABLED = True
        CISCO_EOX_API_AUTO_SYNC_ENABLED = True
        CISCO_EOX_API_QUERIES = "yxcz"

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay()

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message", None) is None
        assert task.info.get("error_message") == "Invalid credentials for Cisco EoX API or insufficient access " \
                                                 "rights (Something is wrong with the credentials handling)"
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"

    def test_api_check_failed(self, monkeypatch):
        # force API failure
        def mock_response():
            raise Exception("The API is broken")

        monkeypatch.setattr(requests, "get", lambda x, headers: mock_response())

        # test automatic trigger
        global CISCO_API_ENABLED
        global CISCO_EOX_API_AUTO_SYNC_ENABLED
        global CISCO_EOX_API_QUERIES
        CISCO_API_ENABLED = True
        CISCO_EOX_API_AUTO_SYNC_ENABLED = True
        CISCO_EOX_API_QUERIES = "yxcz"

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay()

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message", None) is None
        assert task.info.get("error_message") == "Cannot access the Cisco API. Please ensure that the server is " \
                                                 "connected to the internet and that the authentication settings are " \
                                                 "valid."
        assert NotificationMessage.objects.count() == 1, "Task should create a Notification Message"

    def test_periodic_task_enabled_state(self, monkeypatch):
        self.mock_api_call(monkeypatch)

        # test automatic trigger
        global CISCO_API_ENABLED
        global CISCO_EOX_API_AUTO_SYNC_ENABLED
        CISCO_API_ENABLED = True
        CISCO_EOX_API_AUTO_SYNC_ENABLED = False

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay()

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") == "task not enabled"

        CISCO_EOX_API_AUTO_SYNC_ENABLED = True

        task = tasks.execute_task_to_synchronize_cisco_eox_states.delay()

        assert task is not None
        assert task.status == "SUCCESS", task.traceback
        assert task.state == TaskState.SUCCESS
        assert task.info.get("status_message") != "task not enabled"
