"""
py.test configuration file for the test cases in the productdb module
"""
import pytest
from app.productdb import tasks
from app.productdb import views
from django_project import celery


class MockTask:
    def __init__(self):
        self.id = "mock_task_id"


@pytest.fixture
def enable_login_only_mode(monkeypatch):
    """patch the login_required_if_long_only_mode function, which will enable the login only mode"""
    monkeypatch.setattr(views, "login_required_if_login_only_mode", lambda request: True)


@pytest.fixture
def disable_import_price_list_task(monkeypatch):
    """disable the import price list backend function"""
    monkeypatch.setattr(tasks.import_price_list, "delay", lambda **kwargs: MockTask())
    monkeypatch.setattr(celery, "set_meta_data_for_task", lambda: None)
