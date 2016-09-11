"""
Test suite for the django_project.context_processors module
"""
import pytest
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django_project import context_processors

pytestmark = pytest.mark.django_db


class LDAPUserMock:
    ldap_username = "ldap_user"


class LDAPBackendMock:
    def populate_user(self, request):
        return LDAPUserMock()


class TestDjangoProjectContextProcessors:
    @pytest.mark.usefixtures("import_default_users")
    @pytest.mark.usefixtures("import_default_vendors")
    def test_is_ldap_authenticated_user(self, settings, monkeypatch):
        test_user = User.objects.get(username="api")
        rf = RequestFactory()

        request = rf.get(reverse("productdb:home"))
        request.user = test_user

        result = context_processors.is_ldap_authenticated_user(request)

        assert "IS_LDAP_ACCOUNT" in result, "Should provide a variable that indicates that the user is LDAP " \
                                            "authenticated"
        assert result["IS_LDAP_ACCOUNT"] is False

        # when using the LDAP integration, a custom LDAP backend exists for the user
        # if they are readable, the account is an LDAP account
        settings.LDAP_ENABLE = True
        request = rf.get(reverse("productdb:home"))
        request.user = test_user

        result = context_processors.is_ldap_authenticated_user(request)

        assert "IS_LDAP_ACCOUNT" in result
        assert result["IS_LDAP_ACCOUNT"] is False

        # mock the custom LDAP backend
        monkeypatch.setattr(context_processors, "LDAPBackend", LDAPBackendMock)

        request = rf.get(reverse("productdb:home"))
        request.user = test_user

        result = context_processors.is_ldap_authenticated_user(request)

        assert "IS_LDAP_ACCOUNT" in result
        assert result["IS_LDAP_ACCOUNT"] is True
