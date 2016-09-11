"""
Test suite for the ciscoeox.views module
"""
import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from mixer.backend.django import mixer
from app.ciscoeox import api_crawler
from app.ciscoeox import tasks
from app.ciscoeox import views
from app.ciscoeox.exception import CiscoApiCallFailed, ConnectionFailedException
from app.config import AppSettings
from django_project.celery import get_meta_data_for_task

pytestmark = pytest.mark.django_db
MOCK_TASK_ID = "mock_task_id"


class MockTask:
    def __init__(self):
        self.id = MOCK_TASK_ID


@pytest.fixture
def mock_synchronize_task(monkeypatch):
    monkeypatch.setattr(
        tasks.execute_task_to_synchronize_cisco_eox_states,
        "delay",
        lambda ignore_periodic_sync_flag: MockTask()
    )


class TestCiscoEoxQueryView:
    URL_NAME = "cisco_api:eox_query"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.cisco_eox_query(request)

        assert response.status_code == 302

    def test_authenticated_user(self):
        # require super user permissions
        user = mixer.blend("auth.User", is_superuser=False)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user

        with pytest.raises(PermissionDenied):
            views.cisco_eox_query(request)

    def test_superuser_access(self):
        # require super user permissions
        user = mixer.blend("auth.User", is_superuser=True)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user
        response = views.cisco_eox_query(request)

        assert response.status_code == 200

    def test_post_with_api_errors(self, monkeypatch):
        def mock_api_call_failed():
            raise CiscoApiCallFailed()

        def mock_connection_failed_exception():
            raise ConnectionFailedException()

        monkeypatch.setattr(AppSettings, "read_file", lambda self: None)
        monkeypatch.setattr(AppSettings, "is_cisco_api_enabled", lambda self: True)
        monkeypatch.setattr(api_crawler, "update_cisco_eox_database",
                            lambda api_query: mock_api_call_failed())

        user = mixer.blend("auth.User", is_superuser=True)

        url = reverse(self.URL_NAME)
        data = {
            "sync_cisco_eox_states_now": "on",
            "sync_cisco_eox_states_query": "WS-C2960-24T-S"
        }
        request = RequestFactory().post(url, data=data)
        request.user = user
        response = views.cisco_eox_query(request)

        assert response.status_code == 200
        assert "Cisco API call failed" in response.content.decode()

        monkeypatch.setattr(api_crawler, "update_cisco_eox_database",
                            lambda api_query: mock_connection_failed_exception())

        url = reverse(self.URL_NAME)
        data = {
            "sync_cisco_eox_states_now": "on",
            "sync_cisco_eox_states_query": "WS-C2960-24T-S"
        }
        request = RequestFactory().post(url, data=data)
        request.user = user
        response = views.cisco_eox_query(request)

        assert response.status_code == 200
        assert "Cannot contact Cisco API" in response.content.decode()

    def test_post(self, monkeypatch):
        result = [
            {
                "PID": None,
                "blacklist": False,
                "updated": False,
                "created": False,
                "message": "No product update required"
            }
        ]
        monkeypatch.setattr(AppSettings, "read_file", lambda self: None)
        monkeypatch.setattr(AppSettings, "is_cisco_api_enabled", lambda self: True)
        monkeypatch.setattr(api_crawler, "update_cisco_eox_database", lambda api_query: result)

        user = mixer.blend("auth.User", is_superuser=True)

        # test post values without explicit checkbox
        url = reverse(self.URL_NAME)
        data = {
            "sync_cisco_eox_states_query": "WS-C2960-24T-S"
        }
        request = RequestFactory().post(url, data=data)
        request.user = user
        response = views.cisco_eox_query(request)

        assert response.status_code == 200
        assert "No product update required" not in response.content.decode()
        assert "please select the &quot;execute it now" in response.content.decode()

        url = reverse(self.URL_NAME)
        data = {
            "sync_cisco_eox_states_now": "on"
        }
        request = RequestFactory().post(url, data=data)
        request.user = user
        response = views.cisco_eox_query(request)

        assert response.status_code == 200
        assert "Query not specified." in response.content.decode()

        url = reverse(self.URL_NAME)
        data = {
            "sync_cisco_eox_states_now": "on",
            "sync_cisco_eox_states_query": ""
        }
        request = RequestFactory().post(url, data=data)
        request.user = user
        response = views.cisco_eox_query(request)

        assert response.status_code == 200
        assert "Please specify a valid query" in response.content.decode()

        url = reverse(self.URL_NAME)
        data = {
            "sync_cisco_eox_states_now": "on",
            "sync_cisco_eox_states_query": "WS-C29 60-24T-S"
        }
        request = RequestFactory().post(url, data=data)
        request.user = user
        response = views.cisco_eox_query(request)

        assert response.status_code == 200
        assert "Invalid query &#39;WS-C29 60-24T-S&#39;: not executed" in response.content.decode()

        url = reverse(self.URL_NAME)
        data = {
            "sync_cisco_eox_states_now": "on",
            "sync_cisco_eox_states_query": "WS-C2960-24T-S"
        }
        request = RequestFactory().post(url, data=data)
        request.user = user
        response = views.cisco_eox_query(request)

        assert response.status_code == 200
        assert "No product update required" in response.content.decode()


@pytest.mark.usefixtures("mock_synchronize_task")
class TestStartCiscoEoxApiSyncNowView:
    URL_NAME = "cisco_api:start_cisco_eox_api_sync_now"
    TASK_IDENTIFICATION_CACHE_VALUE = "CISCO_EOX_API_SYN_IN_PROGRESS"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.start_cisco_eox_api_sync_now(request)

        assert response.status_code == 302
        assert response.url != "/productdb/task/mock_task_id"

    def test_authenticated_user(self):
        # require super user permissions
        user = mixer.blend("auth.User", is_superuser=False)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user

        with pytest.raises(PermissionDenied):
            views.start_cisco_eox_api_sync_now(request)

    def test_superuser_access(self):
        # require super user permissions
        user = mixer.blend("auth.User", is_superuser=True)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user

        response = views.start_cisco_eox_api_sync_now(request)

        assert response.status_code == 302
        assert response.url == "/productdb/task/mock_task_id"

    def test_start_of_task(self, monkeypatch):
        """
        Test the manual schedule of a synchronization process. To avoid a multiple execution, a cache value is set
        after the process is scheduled. This cache value contains the Task ID to monitor the execution process. If
        a task is already executed, the view should redirect to the process view for the Task ID. Furthermore, a
        meta data object for the task should be created
        """
        user = mixer.blend("auth.User", is_superuser=True)

        # ensure that the task process ID is not set
        cache.delete(self.TASK_IDENTIFICATION_CACHE_VALUE)

        # get call to create task (should not run because no task backend is active at this point in time
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user
        response = views.start_cisco_eox_api_sync_now(request)

        assert response.status_code == 302
        assert response.url == "/productdb/task/mock_task_id"
        assert get_meta_data_for_task(task_id="mock_task_id") == {
            "auto_redirect": False,
            "redirect_to": "/productdb/config/status/",
            "title": "Synchronize local database with Cisco EoX API"
        }

        # mock task schedule to raise an exception if called (verify that really the redirect works)
        def raise_exception():
            raise Exception("should never happen")

        monkeypatch.setattr(
            tasks.execute_task_to_synchronize_cisco_eox_states,
            "delay",
            lambda ignore_periodic_sync_flag: raise_exception()
        )

        # verify redirect
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user
        response = views.start_cisco_eox_api_sync_now(request)

        assert response.status_code == 302
        assert response.url == "/productdb/task/mock_task_id"
