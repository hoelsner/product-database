"""
Test suite for the django_project.views module
"""
import json
import pytest
import redis
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from mixer.backend.django import mixer
from django_project.celery import app, TaskState
from django_project import context_processors
from django_project import views
from django_project.celery import set_meta_data_for_task

pytestmark = pytest.mark.django_db


@pytest.fixture
def enable_login_only_mode(monkeypatch):
    """patch the login_required_if_long_only_mode function, which will enable the login only mode"""
    monkeypatch.setattr(views, "login_required_if_login_only_mode", lambda request: True)


@pytest.mark.usefixtures("import_default_vendors")
class TestCustomPageViews:
    def test_custom_page_not_found(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        response = views.custom_page_not_found_view(request)

        assert response.status_code == 404

    def test_custom_page_not_found_view(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        response = views.custom_error_view(request)

        assert response.status_code == 500

    def test_custom_bad_request_view(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        response = views.custom_bad_request_view(request)

        assert response.status_code == 400

    def test_custom_permission_denied_view(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        response = views.custom_permission_denied_view(request)

        assert response.status_code == 403

    def test_custom_csrf_failure_page(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        response = views.custom_csrf_failure_page(request)

        assert response.status_code == 200
        assert "Form expired" in response.content.decode()


@pytest.mark.usefixtures("import_default_vendors")
class TestPasswordChangeView:
    URL_NAME = "change_password"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.custom_password_change(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)
        response = views.custom_password_change(request)

        assert response.status_code == 200, "Should be callable"

    def test_authenticated_ldap_user(self, monkeypatch, settings):
        """LDAP users are not allowed to change there passwords, this must happen in the directory itself"""
        # when using the LDAP integration, a custom LDAP backend exists for the user
        # if they are readable, the account is an LDAP account
        settings.LDAP_ENABLE = True

        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)
        request.user.ldap_user = True

        response = views.custom_password_change(request)

        assert response.status_code == 403


@pytest.mark.usefixtures("import_default_vendors")
class TestPasswordChangeDoneView:
    URL_NAME = "custom_password_change_done"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.custom_password_change_done(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)
        response = views.custom_password_change_done(request)

        assert response.status_code == 200, "Should be callable"

    def test_authenticated_ldap_user(self, monkeypatch, settings):
        """LDAP users are not allowed to change there passwords, this must happen in the LDAP directory itself"""
        # when using the LDAP integration, a custom LDAP backend exists for the user
        # if they are readable, the account is an LDAP account
        settings.LDAP_ENABLE = True

        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)
        request.user.ldap_user = True

        response = views.custom_password_change_done(request)

        assert response.status_code == 403


@pytest.mark.usefixtures("import_default_vendors")
class TestLoginLogoutView:
    URL_NAME = "login"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()

        response = views.login_user(request)

        assert response.status_code == 200

    def test_authenticated_user(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)

        response = views.login_user(request)

        assert response.status_code == 302, "Should redirect to homepage"
        assert response.url == reverse("productdb:home")

    def test_authenticated_user_logout(self):
        url = reverse("logout")
        request = RequestFactory().get(url)
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        response = views.logout_user(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login")

    @pytest.mark.usefixtures("import_default_users")
    @pytest.mark.usefixtures("import_default_vendors")
    def test_login_default(self):
        url = reverse(self.URL_NAME)
        data = {
            "username": "api",
            "password": "api"
        }
        request = RequestFactory().post(url, data=data)
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        response = views.login_user(request)

        assert response.status_code == 302
        assert response.url == reverse("productdb:home")

    @pytest.mark.usefixtures("import_default_users")
    @pytest.mark.usefixtures("import_default_vendors")
    def test_login_ignore_next_login_link(self):
        url = reverse(self.URL_NAME)
        data = {
            "username": "api",
            "password": "api"
        }
        request = RequestFactory().post(url + "?next=/productdb/login", data=data)
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        response = views.login_user(request)

        assert response.status_code == 302
        assert response.url == reverse("productdb:home"), "Should ignore the redirect to the login link"

    @pytest.mark.usefixtures("import_default_users")
    @pytest.mark.usefixtures("import_default_vendors")
    def test_login_with_next_link(self):
        url = reverse(self.URL_NAME)
        data = {
            "username": "api",
            "password": "api"
        }
        request = RequestFactory().post(url + "?next=/xyz", data=data)
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        response = views.login_user(request)

        assert response.status_code == 302
        assert response.url == "/xyz"

    @pytest.mark.usefixtures("import_default_users")
    @pytest.mark.usefixtures("import_default_vendors")
    def test_login_failed(self):
        url = reverse(self.URL_NAME)
        data = {
            "username": "api",
            "password": "invalid password"
        }
        request = RequestFactory().post(url, data=data)
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        response = views.login_user(request)

        assert response.status_code == 200
        assert "Login failed, invalid credentials" in response.content.decode()

    @pytest.mark.usefixtures("import_default_users")
    @pytest.mark.usefixtures("import_default_vendors")
    def test_login_disabled_account(self):
        u = User.objects.get(username="api")
        u.is_active = False
        u.save()

        url = reverse(self.URL_NAME)
        data = {
            "username": "api",
            "password": "api"
        }
        request = RequestFactory().post(url, data=data)
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        response = views.login_user(request)

        assert response.status_code == 200
        assert "Login failed, invalid credentials" in response.content.decode()


@pytest.mark.usefixtures("import_default_vendors")
@pytest.mark.usefixtures("redis_server_required")
class TestProgressView:
    URL_NAME = "task_in_progress"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME, kwargs={"task_id": "mock_task_id"})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.task_progress_view(request, "mock_task_id")

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME, kwargs={"task_id": "mock_task_id"})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.task_progress_view(request, "mock_task_id")

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        url = reverse(self.URL_NAME, kwargs={"task_id": "mock_task_id"})
        request = RequestFactory().get(url)
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)
        response = views.task_progress_view(request, "mock_task_id")

        assert response.status_code == 200, "Should be callable"

    def test_reaction_on_task_meta_data(self):
        # the redirect behavior is tested within the selenium test cases
        set_meta_data_for_task(
            task_id="mock_task_id",
            title="My Test Task",
            redirect_to=reverse("productdb:home")
        )
        url = reverse(self.URL_NAME, kwargs={"task_id": "mock_task_id"})
        request = RequestFactory().get(url)
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)
        response = views.task_progress_view(request, "mock_task_id")

        assert response.status_code == 200, "Should be callable"
        assert "My Test Task" in response.content.decode()


@pytest.mark.usefixtures("import_default_vendors")
class TestStatusAjaxCall:
    URL_NAME = "task_state"

    def test_anonymous_default(self, monkeypatch):
        class MockAsyncResult:
            state = TaskState.PENDING

        monkeypatch.setattr(app, "AsyncResult", lambda task_id: MockAsyncResult())

        url = reverse(self.URL_NAME, kwargs={"task_id": "mock_task_id"})
        request = RequestFactory().get(url)
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # AJAX request
        request.user = AnonymousUser()

        response = views.task_status_ajax(request, "mock_task_id")

        assert response.status_code == 200, "Should be callable"
        assert json.loads(response.content.decode()) == {"state": "pending", "status_message": "try to start task"}

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self, monkeypatch):
        class MockAsyncResult:
            state = TaskState.PENDING

        monkeypatch.setattr(app, "AsyncResult", lambda task_id: MockAsyncResult())

        url = reverse(self.URL_NAME, kwargs={"task_id": "mock_task_id"})
        request = RequestFactory().get(url)
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # AJAX request
        request.user = AnonymousUser()

        response = views.task_status_ajax(request, "mock_task_id")

        assert response.status_code == 200, "Should be callable"
        assert json.loads(response.content.decode()) == {"state": "pending", "status_message": "try to start task"}

    def test_authenticated_user(self, monkeypatch):
        class MockAsyncResult:
            state = TaskState.PENDING

        monkeypatch.setattr(app, "AsyncResult", lambda task_id: MockAsyncResult())

        url = reverse(self.URL_NAME, kwargs={"task_id": "mock_task_id"})
        request = RequestFactory().get(url)
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # AJAX request
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)

        response = views.task_status_ajax(request, "mock_task_id")

        assert response.status_code == 200, "Should be callable"
        assert json.loads(response.content.decode()) == {"state": "pending", "status_message": "try to start task"}

    def test_started_task_state(self, monkeypatch):
        class MockAsyncResult:
            state = TaskState.STARTED
            info = {
                "status_message": "no state"
            }

        monkeypatch.setattr(app, "AsyncResult", lambda task_id: MockAsyncResult())

        url = reverse(self.URL_NAME, kwargs={"task_id": "mock_task_id"})
        request = RequestFactory().get(url)
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # AJAX request
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)

        response = views.task_status_ajax(request, "mock_task_id")

        assert response.status_code == 200, "Should be callable"
        assert json.loads(response.content.decode()) == {"state": "processing", "status_message": "no state"}

    def test_success_task_state_without_error(self, monkeypatch):
        class MockAsyncResult:
            state = TaskState.SUCCESS
            info = {
                "status_message": "again, no state"
            }

        monkeypatch.setattr(app, "AsyncResult", lambda task_id: MockAsyncResult())

        url = reverse(self.URL_NAME, kwargs={"task_id": "mock_task_id"})
        request = RequestFactory().get(url)
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # AJAX request
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)

        response = views.task_status_ajax(request, "mock_task_id")

        assert response.status_code == 200, "Should be callable"
        assert json.loads(response.content.decode()) == {"state": "success", "status_message": "again, no state"}

    def test_success_task_state_without_error_and_custom_data(self, monkeypatch):
        class MockAsyncResult:
            state = TaskState.SUCCESS
            info = {
                "status_message": "again, no state",
                "data": {
                    "what?": "just some custom information"
                }
            }

        monkeypatch.setattr(app, "AsyncResult", lambda task_id: MockAsyncResult())

        url = reverse(self.URL_NAME, kwargs={"task_id": "mock_task_id"})
        request = RequestFactory().get(url)
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # AJAX request
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)

        response = views.task_status_ajax(request, "mock_task_id")

        assert response.status_code == 200, "Should be callable"
        assert json.loads(response.content.decode()) == {
            "state": "success",
            "status_message": "again, no state",
            "data": {
                "what?": "just some custom information"
            }
        }

    def test_success_task_state_with_error(self, monkeypatch):
        """The task itself was successful, but the result was an error"""
        class MockAsyncResult:
            state = TaskState.SUCCESS
            info = {
                "error_message": "something went wrong"
            }

        monkeypatch.setattr(app, "AsyncResult", lambda task_id: MockAsyncResult())

        url = reverse(self.URL_NAME, kwargs={"task_id": "mock_task_id"})
        request = RequestFactory().get(url)
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # AJAX request
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)

        response = views.task_status_ajax(request, "mock_task_id")

        assert response.status_code == 200, "Should be callable"
        assert json.loads(response.content.decode()) == {
            "state": "success", "status_message": "", "error_message": "something went wrong"
        }

    def test_failed_task_state(self, monkeypatch):
        """The task was not successful completed (traceback)"""
        class MockAsyncResult:
            state = TaskState.FAILED
            info = "TRACEBACK"

        monkeypatch.setattr(app, "AsyncResult", lambda task_id: MockAsyncResult())

        url = reverse(self.URL_NAME, kwargs={"task_id": "mock_task_id"})
        request = RequestFactory().get(url)
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # AJAX request
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)

        response = views.task_status_ajax(request, "mock_task_id")

        assert response.status_code == 200, "Should be callable"
        assert json.loads(response.content.decode()) == {
            "state": "failed", "error_message": "TRACEBACK"
        }

    def test_failed_redis_connection(self, monkeypatch):
        """redis not available"""
        def raise_exception():
            raise redis.ConnectionError()

        monkeypatch.setattr(app, "AsyncResult", lambda task_id: raise_exception())

        url = reverse(self.URL_NAME, kwargs={"task_id": "mock_task_id"})
        request = RequestFactory().get(url)
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"  # AJAX request
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)

        response = views.task_status_ajax(request, "mock_task_id")

        assert response.status_code == 200, "Should be callable"
        assert json.loads(response.content.decode()) == {
            "state": "failed",
            "error_message": "A server process (redis) is not running, please contact the administrator"
        }

    def test_call_with_unknown_task(self):
        url = reverse(self.URL_NAME, kwargs={"task_id": "mock_task_id"})
        request = RequestFactory().get(url)
        request.user = mixer.blend("auth.User", is_superuser=False, is_staff=False)
        response = views.task_status_ajax(request, "mock_task_id")

        assert response.status_code == 400
