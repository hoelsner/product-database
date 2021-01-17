"""
Test suite for the config.views module
"""
import pytest
from html import escape
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.http import Http404
from django.test import RequestFactory
from django_project import celery
from app.config import views
from app.config import models
from app.config import utils
from app.config.settings import AppSettings

pytestmark = pytest.mark.django_db


def patch_contrib_messages(request):
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)

    return messages


@pytest.fixture
def mock_cisco_eox_api_access_available(monkeypatch):
    app = AppSettings()
    app.set_cisco_api_enabled(True)
    app.set_cisco_api_client_id("client_id")
    app.set_cisco_api_client_id("client_secret")
    app.set_periodic_sync_enabled(True)
    app.set_cisco_eox_api_queries("")
    app.set_product_blacklist_regex("")
    app.set_auto_create_new_products(True)

    monkeypatch.setattr(utils, "check_cisco_eox_api_access",
                        lambda client_id, client_secret, drop_credentials=False: True)


@pytest.fixture
def mock_cisco_eox_api_access_broken(monkeypatch):
    app = AppSettings()
    app.set_cisco_api_enabled(True)
    app.set_cisco_api_client_id("client_id")
    app.set_cisco_api_client_id("client_secret")
    app.set_periodic_sync_enabled(True)
    app.set_cisco_eox_api_queries("")
    app.set_product_blacklist_regex("")
    app.set_auto_create_new_products(True)

    monkeypatch.setattr(utils, "check_cisco_eox_api_access",
                        lambda client_id, client_secret, drop_credentials=False: False)


@pytest.fixture
def mock_cisco_eox_api_access_exception(monkeypatch):
    def raise_exception():
        raise Exception("totally broken")

    app = AppSettings()
    app.set_cisco_api_enabled(True)
    app.set_cisco_api_client_id("client_id")
    app.set_cisco_api_client_id("client_secret")
    app.set_periodic_sync_enabled(True)
    app.set_cisco_eox_api_queries("")
    app.set_product_blacklist_regex("")
    app.set_auto_create_new_products(True)

    monkeypatch.setattr(utils, "check_cisco_eox_api_access",
                        lambda client_id, client_secret, drop_credentials: raise_exception())


@pytest.fixture
def mock_cisco_eox_api_access_disabled():
    app = AppSettings()
    app.set_cisco_api_enabled(False)


@pytest.mark.usefixtures("import_default_vendors")
class TestAddNotificationView:
    URL_NAME = "productdb_config:notification-add"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.add_notification(request)

        assert response.status_code == 302
        assert response.url.startswith("/productdb/login")

    def test_authenticated_user(self):
        # require super user permissions
        user = User.objects.create(username="username", is_superuser=False)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user

        with pytest.raises(PermissionDenied):
            views.add_notification(request)

    def test_superuser_access(self):
        # require super user permissions
        user = User.objects.create(username="username", is_superuser=True)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user

        response = views.add_notification(request)

        assert response.status_code == 200

    def test_post(self):
        # require super user permissions
        user = User.objects.create(username="username", is_superuser=True)
        url = reverse(self.URL_NAME)
        data = {
            "title": "MyTitle",
            "type": "ERR",
            "summary_message": "This is a summary",
            "detailed_message": "This is the detail message"
        }
        request = RequestFactory().post(url, data=data)
        request.user = user

        response = views.add_notification(request)

        assert response.status_code == 302
        assert models.NotificationMessage.objects.count() == 1
        n = models.NotificationMessage.objects.filter(title="MyTitle").first()
        assert n.type == models.NotificationMessage.MESSAGE_ERROR

        # test with missing input
        data = {
            "title": "MyTitle",
            "type": "ERR",
            "detailed_message": "This is the detail message"
        }
        request = RequestFactory().post(url, data=data)
        request.user = user

        response = views.add_notification(request)

        assert response.status_code == 200


@pytest.mark.usefixtures("import_default_vendors")
class TestStatusView:
    URL_NAME = "productdb_config:status"

    @pytest.mark.usefixtures("mock_cisco_eox_api_access_available")
    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.status(request)

        assert response.status_code == 302
        assert response.url.startswith("/productdb/login")

    @pytest.mark.usefixtures("mock_cisco_eox_api_access_available")
    def test_authenticated_user(self):
        # require super user permissions
        user = User.objects.create(username="username", is_superuser=False)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user

        with pytest.raises(PermissionDenied):
            views.status(request)

    @pytest.mark.usefixtures("mock_cisco_eox_api_access_available")
    @pytest.mark.usefixtures("mock_worker_not_available_state")
    def test_superuser_access(self):
        # require super user permissions
        user = User.objects.create(username="username", is_superuser=True)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user
        response = views.status(request)

        assert response.status_code == 200
        expected_content = [
            "No backend worker found, asynchronous and scheduled tasks are not executed.",
            "successful connected to the Cisco EoX API"
        ]
        page_content = response.content.decode()
        for line in expected_content:
            assert line in page_content, page_content

        assert cache.get("CISCO_EOX_API_TEST", None) is True

        # cleanup
        cache.delete("CISCO_EOX_API_TEST")

    @pytest.mark.usefixtures("mock_cisco_eox_api_access_available")
    def test_with_active_workers(self, monkeypatch):
        monkeypatch.setattr(celery, "is_worker_active", lambda: True)
        cache.delete("CISCO_EOX_API_TEST")  # ensure that cache is not set

        # require super user permissions
        user = User.objects.create(username="username", is_superuser=True)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user

        response = views.status(request)

        assert response.status_code == 200
        assert cache.get("CISCO_EOX_API_TEST", None) is True
        expected_content = [
            "Backend worker found.",
            "successful connected to the Cisco EoX API"
        ]

        for line in expected_content:
            assert line in response.content.decode()

        # cleanup
        cache.delete("CISCO_EOX_API_TEST")

    @pytest.mark.usefixtures("mock_cisco_eox_api_access_available")
    def test_with_inactive_workers(self, monkeypatch):
        monkeypatch.setattr(celery, "is_worker_active", lambda: False)
        cache.delete("CISCO_EOX_API_TEST")  # ensure that cache is not set

        # require super user permissions
        user = User.objects.create(username="username", is_superuser=True)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user

        response = views.status(request)

        assert response.status_code == 200
        assert cache.get("CISCO_EOX_API_TEST", None) is True
        expected_content = [
            "No backend worker found, asynchronous and scheduled tasks are not executed.",
            "successful connected to the Cisco EoX API"
        ]
        for line in expected_content:
            assert line in response.content.decode()

        # cleanup
        cache.delete("CISCO_EOX_API_TEST")

    @pytest.mark.usefixtures("mock_cisco_eox_api_access_broken")
    def test_access_with_broken_api(self):
        # require super user permissions
        user = User.objects.create(username="username", is_superuser=True)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user

        response = views.status(request)

        assert response.status_code == 200
        assert cache.get("CISCO_EOX_API_TEST", None) is False

        # cleanup
        cache.delete("CISCO_EOX_API_TEST")

    @pytest.mark.usefixtures("mock_cisco_eox_api_access_exception")
    def test_access_with_broken_api_by_exception(self):
        # require super user permissions
        user = User.objects.create(username="username", is_superuser=True)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user

        response = views.status(request)

        assert response.status_code == 200
        assert cache.get("CISCO_EOX_API_TEST", None) is None

        # cleanup
        cache.delete("CISCO_EOX_API_TEST")


@pytest.mark.usefixtures("import_default_vendors")
class TestChangeConfiguration:
    URL_NAME = "productdb_config:change_settings"

    @pytest.mark.usefixtures("mock_cisco_eox_api_access_available")
    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.change_configuration(request)

        assert response.status_code == 302
        assert response.url.startswith("/productdb/login")

    @pytest.mark.usefixtures("mock_cisco_eox_api_access_available")
    def test_authenticated_user(self):
        # require super user permissions
        user = User.objects.create(username="username", is_superuser=False)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user

        with pytest.raises(PermissionDenied):
            views.change_configuration(request)

    @pytest.mark.usefixtures("mock_cisco_eox_api_access_available")
    @pytest.mark.usefixtures("import_default_text_blocks")
    def test_superuser_access(self):
        # require super user permissions
        user = User.objects.create(username="username", is_superuser=True)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user
        patch_contrib_messages(request)

        response = views.change_configuration(request)

        assert response.status_code == 200

        for content in models.TextBlock.objects.all().values_list("html_content", flat=True):
            assert escape(content) in response.content.decode()

    def test_global_options_are_visible(self):
        app_config = AppSettings()
        test_internal_id = "My custom Internal ID"
        app_config.set_internal_product_id_label(test_internal_id)

        # require super user permissions
        user = User.objects.create(username="username", is_superuser=True)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user
        patch_contrib_messages(request)

        response = views.change_configuration(request)

        assert response.status_code == 200
        assert test_internal_id in response.content.decode()

    @pytest.mark.usefixtures("mock_cisco_eox_api_access_available")
    @pytest.mark.usefixtures("import_default_text_blocks")
    def test_post_with_active_api(self):
        # require super user permissions
        user = User.objects.create(username="username", is_superuser=True)
        url = reverse(self.URL_NAME)
        data = {}
        request = RequestFactory().post(url, data=data)
        request.user = user
        patch_contrib_messages(request)

        response = views.change_configuration(request)

        assert response.status_code == 302
        assert response.url == "/productdb/config/change/"

        # test with invalid post value
        data = {
            "cisco_api_enabled": "on",
            "cisco_api_client_id": "client_id",
            "eox_api_blacklist": "("
        }
        request = RequestFactory().post(url, data=data)
        request.user = user
        msgs = patch_contrib_messages(request)

        response = views.change_configuration(request)

        assert response.status_code == 200
        assert msgs.added_new

        data = {
            "cisco_api_client_id": "my changed client ID",
            "cisco_api_client_secret": "my changed client secret",
        }
        request = RequestFactory().post(url, data=data)
        request.user = user
        patch_contrib_messages(request)

        response = views.change_configuration(request)

        assert response.status_code == 302
        assert response.url == "/productdb/config/change/"

    @pytest.mark.usefixtures("mock_cisco_eox_api_access_disabled")
    @pytest.mark.usefixtures("import_default_text_blocks")
    def test_post_with_inactive_api(self):
        # require super user permissions
        user = User.objects.create(username="username", is_superuser=True)
        url = reverse(self.URL_NAME)
        data = {
            "cisco_api_enabled": "on",
        }
        request = RequestFactory().post(url, data=data)
        request.user = user
        msgs = patch_contrib_messages(request)

        response = views.change_configuration(request)

        assert response.status_code == 302
        assert response.url == "/productdb/config/change/"
        assert msgs.added_new

        data = {
            "cisco_api_enabled": "on",
            "cisco_api_client_id": "client_id"
        }
        request = RequestFactory().post(url, data=data)
        request.user = user
        msgs = patch_contrib_messages(request)

        response = views.change_configuration(request)

        assert response.status_code == 302
        assert response.url == "/productdb/config/change/"
        assert msgs.added_new

    @pytest.mark.usefixtures("mock_cisco_eox_api_access_disabled")
    @pytest.mark.usefixtures("import_default_text_blocks")
    def test_post_with_broken_api(self):
        # require super user permissions
        user = User.objects.create(username="username", is_superuser=True)
        url = reverse(self.URL_NAME)
        data = {
            "cisco_api_enabled": "on",
            "cisco_api_client_id": "client_id"
        }
        request = RequestFactory().post(url, data=data)
        request.user = user
        msgs = patch_contrib_messages(request)

        response = views.change_configuration(request)

        assert response.status_code == 302
        assert response.url == "/productdb/config/change/"
        assert msgs.added_new


@pytest.mark.usefixtures("import_default_vendors")
class TestServerMessagesList:
    URL_NAME = "productdb_config:notification-list"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.server_messages_list(request)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.server_messages_list(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        models.NotificationMessage.objects.create(title="A1", summary_message="B", detailed_message="C")
        models.NotificationMessage.objects.create(title="A2", summary_message="B", detailed_message="C")
        models.NotificationMessage.objects.create(title="A3", summary_message="B", detailed_message="C")
        models.NotificationMessage.objects.create(title="A4", summary_message="B", detailed_message="C")
        models.NotificationMessage.objects.create(title="A5", summary_message="B", detailed_message="C")
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="username", is_superuser=False, is_staff=False)
        response = views.server_messages_list(request)

        assert response.status_code == 200, "Should be callable"


@pytest.mark.usefixtures("import_default_vendors")
class TestServerMessagesDetail:
    URL_NAME = "productdb_config:notification-detail"

    def test_anonymous_default(self):
        nm = models.NotificationMessage.objects.create(title="A1", summary_message="B", detailed_message="C")

        url = reverse(self.URL_NAME, kwargs={"message_id": nm.id})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.server_message_detail(request, nm.id)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        nm = models.NotificationMessage.objects.create(title="A1", summary_message="B", detailed_message="C")

        url = reverse(self.URL_NAME, kwargs={"message_id": nm.id})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.server_message_detail(request, nm.id)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        nm = models.NotificationMessage.objects.create(title="A1", summary_message="B", detailed_message="C")

        url = reverse(self.URL_NAME, kwargs={"message_id": nm.id})
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="username", is_superuser=False, is_staff=False)
        response = views.server_message_detail(request, nm.id)

        assert response.status_code == 200, "Should be callable"

    def test_404(self):
        url = reverse(self.URL_NAME, kwargs={"message_id": 9999})
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="username", is_superuser=False, is_staff=False)

        with pytest.raises(Http404):
            views.server_message_detail(request, 9999)


@pytest.mark.usefixtures("import_default_vendors")
class TestFlushCache:
    URL_NAME = "productdb_config:flush_cache"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.flush_cache(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.flush_cache(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="username", is_superuser=False, is_staff=False)

        with pytest.raises(PermissionDenied):
            views.flush_cache(request)

    @pytest.mark.usefixtures("import_default_users")
    @pytest.mark.usefixtures("import_default_vendors")
    def test_superuser(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = User.objects.get(username="pdb_admin")
        msgs = patch_contrib_messages(request)
        response = views.flush_cache(request)

        assert response.status_code == 302, "Should redirect to status page"
        assert msgs.added_new
        assert response.url == reverse("productdb_config:status")

