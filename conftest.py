import json
import pytest
import redis
import requests
from cacheops import invalidate_all
from django.core.management import call_command
from django.core.cache import cache
from requests import Response
from app.config.settings import AppSettings
from app.config import utils

CISCO_API_TEST_CREDENTIALS_FILE = ".cisco_api_credentials"


def pytest_addoption(parser):
    # requires test credentials in the working directory named .cisco_api_credentials
    parser.addoption("--online", action="store_true", help="run tests online (with external API access)")
    parser.addoption("--selenium", action="store_true", help="execute selenium based test cases against a test "
                                                             "instance")


@pytest.fixture
def redis_server_required():
    rs = redis.Redis("localhost")
    try:
        _ = rs.client_list()
    except redis.ConnectionError:
        pytest.fail("Redis server not running on localhost")


@pytest.fixture
def set_celery_always_eager(settings):
    """enable celery eager mode (tasks run not asynchronous"""
    settings.CELERY_ALWAYS_EAGER = True
    settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True


@pytest.fixture
def load_test_cisco_api_credentials():
    with open(CISCO_API_TEST_CREDENTIALS_FILE) as f:
        cred = json.loads(f.read())

    app = AppSettings()
    app.set_cisco_api_client_id(cred["client_id"])
    app.set_cisco_api_client_secret(cred["client_secret"])


@pytest.fixture
def import_default_vendors(django_db_setup, django_db_blocker):
    """import default vendors from YAML fixture"""
    # load default_vendors.yaml fixture
    with django_db_blocker.unblock():
        call_command("loaddata", "default_vendors.yaml", verbosity=0)


@pytest.fixture
def import_default_users(django_db_setup, django_db_blocker):
    """import default users from YAML fixture"""
    # load default_users.yaml fixture
    with django_db_blocker.unblock():
        call_command("loaddata", "default_users.yaml", verbosity=0)


@pytest.fixture
def import_default_text_blocks(django_db_setup, django_db_blocker):
    """import default users from YAML fixture"""
    # load default_users.yaml fixture
    with django_db_blocker.unblock():
        call_command("loaddata", "default_text_blocks.yaml", verbosity=0)


@pytest.fixture
def mock_cisco_api_authentication_server(monkeypatch):
    """mock a successful Cisco API authentication server response"""
    def mock_post_response():
        r = Response()
        r.status_code = 200
        r.encoding = "UTF-8"
        r._content = str(json.dumps({
            "access_token": "access_token",
            "token_type": "Bearer",
            "expires_in": 3599
        })).encode("UTF-8")

        return r

    monkeypatch.setattr(utils, "check_cisco_eox_api_access", lambda x, y, z: True)
    monkeypatch.setattr(utils, "check_cisco_hello_api_access", lambda x, y, z: True)
    monkeypatch.setattr(
        requests,
        "post",
        lambda url, params=None, proxies=None: mock_post_response()
    )


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.yield_fixture(autouse=True)
def flush_cache():
    """delete all cached data"""
    cache.clear()
    invalidate_all()
