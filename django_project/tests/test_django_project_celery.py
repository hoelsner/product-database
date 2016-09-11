"""
Test suite for the django_project.celery module
"""
import pytest
import uuid
from django_project import celery

pytestmark = pytest.mark.django_db


class TestCustomMetaData:
    def test_get_invalid_task_meta_data(self):
        result = celery.get_meta_data_for_task("invalid id")

        assert result == {}

    def test_custom_celery_task_meta_data(self):
        # custom meta data are used for the process watch view
        test_task_id = uuid.uuid4()
        test_title = "Custom Title"
        celery.set_meta_data_for_task(test_task_id, test_title)

        result = celery.get_meta_data_for_task(test_task_id)

        assert type(result) is dict
        assert "title" in result
        assert "auto_redirect" in result
        assert "redirect_to" not in result
        assert result["title"] == test_title
        assert result["auto_redirect"] is True

    def test_custom_celery_task_meta_data_with_redirect(self):
        # custom meta data are used for the process watch view
        test_task_id = uuid.uuid4()
        test_title = "Custom Title"
        test_redirect = "/productdb/"
        celery.set_meta_data_for_task(test_task_id, test_title, redirect_to=test_redirect)

        result = celery.get_meta_data_for_task(test_task_id)

        assert type(result) is dict
        assert "title" in result
        assert "auto_redirect" in result
        assert "redirect_to" in result
        assert result["title"] == test_title
        assert result["auto_redirect"] is True, "Auto redirect should be enabled by default"
        assert result["redirect_to"] == test_redirect

    def test_custom_celery_task_meta_data_without_auto_redirect(self):
        # custom meta data are used for the process watch view
        test_task_id = uuid.uuid4()
        test_title = "Custom Title"
        test_redirect = "/productdb/"
        celery.set_meta_data_for_task(test_task_id, test_title, redirect_to=test_redirect, auto_redirect=False)

        result = celery.get_meta_data_for_task(test_task_id)

        assert type(result) is dict
        assert "title" in result
        assert "auto_redirect" in result
        assert "redirect_to" in result
        assert result["title"] == test_title
        assert result["auto_redirect"] is False
        assert result["redirect_to"] == test_redirect
