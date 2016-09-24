"""
py.test configuration file for the test cases in the config module
"""
import pytest
from app.config import views
from app.config.tests import CONFIG_FILE_PATH


@pytest.fixture
def enable_login_only_mode(monkeypatch):
    """patch the login_required_if_long_only_mode function, which will enable the login only mode"""
    monkeypatch.setattr(views, "login_required_if_login_only_mode", lambda request: True)
