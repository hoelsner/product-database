"""
custom context processors for the page
"""
from django_auth_ldap.backend import LDAPBackend
from django.conf import settings


def is_ldap_authenticated_user(request):
    """
    injects an IS_LDAP_ACCOUNT
    """
    result = False
    try:
        if settings.LDAP_ENABLE:
            # try to get the username
            user = LDAPBackend().populate_user(request.user.get_username())

            # try to access the ldap_username (if this raises an exception, the user is not an LDAP user)
            val = user.ldap_username
            result = True

    except Exception as ex:
        # cannot get user info, assume that this is not an LDAP account
        pass

    return {
        "IS_LDAP_ACCOUNT": result
    }
