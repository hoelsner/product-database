import pytest
import redis
from django.core.management import call_command


def pytest_addoption(parser):
    # requires test credentials in the working directory named .cisco_api_credentials
    parser.addoption("--online", action="store_true", help="run tests online (with external API access)")
    parser.addoption("--selenium", action="store_true", help="run selenium test cases (always online)")


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
