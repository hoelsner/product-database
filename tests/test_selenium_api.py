"""
Test suite for the selenium test cases
"""
import pytest
from tests import BaseSeleniumTest

pytestmark = pytest.mark.django_db
selenium_test = pytest.mark.skipif(not pytest.config.getoption("--selenium"), reason="need --selenium to run")


@selenium_test
class TestCommonApiViews(BaseSeleniumTest):
    def test_swagger_ui_has_no_500(self, browser, live_server):
        browser.get(live_server + "/productdb/api-docs/")

        page_text = browser.find_element_by_tag_name('body').text

        assert "INTERNAL SERVER ERROR" not in page_text, "No internal server error is visible"
