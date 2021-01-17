"""
py.test configuration file for the test cases in the config module
"""
import pytest
from app.config import views, utils


@pytest.fixture
def enable_login_only_mode(monkeypatch):
    """patch the login_required_if_long_only_mode function, which will enable the login only mode"""
    monkeypatch.setattr(views, "login_required_if_login_only_mode", lambda request: True)


@pytest.fixture
def mock_worker_not_available_state(monkeypatch):
    """patch the utils.get_celery_worker_state_html to respond only that the worker process is not available"""
    monkeypatch.setattr(
        utils,
        "get_celery_worker_state_html",
        lambda: """
            <div class="alert alert-danger" role="alert">
                <span class="fa fa-exclamation-circle"></span>
                No backend worker found, asynchronous and scheduled tasks are not executed.
            </div>"""
    )
