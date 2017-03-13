"""
configure optional LDAP settings
"""
import logging
import os
import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType


LDAP_ENABLE = os.getenv("PDB_LDAP_ENABLE", False)

if LDAP_ENABLE:
    logging.getLogger().warning("LDAP authentication enabled on server")

    AUTH_LDAP_SERVER_URI = os.getenv("PDB_LDAP_SERVER_URL", "ldap://127.0.0.1:389/")
    AUTH_LDAP_BIND_DN = os.getenv("PDB_LDAP_BIND_DN", "cn=django-agent,dc=example,dc=com")
    AUTH_LDAP_BIND_PASSWORD = os.getenv("PDB_LDAP_BIND_PASSWORD", "")

    AUTH_LDAP_USER_SEARCH = LDAPSearch(os.getenv("PDB_LDAP_USER_SEARCH", "ou=users,dc=example,dc=com"),
                                       ldap.SCOPE_SUBTREE, "(uid=%(user)s)")

    AUTH_LDAP_GROUP_SEARCH = LDAPSearch(os.getenv("PDB_LDAP_GROUP_SEARCH", ""),
                                        ldap.SCOPE_SUBTREE, "(objectClass=groupOfNames)"
                                        )
    AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()

    AUTH_LDAP_REQUIRE_GROUP = os.getenv("PDB_LDAP_REQUIRE_GROUP", "")

    # Populate the Django user from the LDAP directory.
    AUTH_LDAP_USER_ATTR_MAP = {
        "email": "mail"
    }

    AUTH_LDAP_FIND_GROUP_PERMS = True
    AUTH_LDAP_CACHE_GROUPS = True
    AUTH_LDAP_GROUP_CACHE_TIMEOUT = 15 * 60

    # enable LDAP authentication along with the Model Backend (fallback to local DB authentication is enabled by
    # default)
    AUTHENTICATION_BACKENDS = (
        'django_auth_ldap.backend.LDAPBackend',
        'django.contrib.auth.backends.ModelBackend',
    )
