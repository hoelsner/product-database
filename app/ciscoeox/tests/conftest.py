import pytest
from app.config.settings import AppSettings


@pytest.fixture
def enable_cisco_api():
    app = AppSettings()
    app.set_cisco_api_enabled(True)


@pytest.fixture
def enabled_autocreate_new_products():
    app = AppSettings()
    app.set_auto_create_new_products(True)


@pytest.fixture
def disable_cisco_api():
    app = AppSettings()
    app.set_cisco_api_enabled(False)
