"""
Test suite for the selenium test cases
"""
import os
import pytest
from django.core.urlresolvers import reverse
from selenium.webdriver.common.keys import Keys
from tests import BaseSeleniumTest

pytestmark = pytest.mark.django_db
selenium_test = pytest.mark.skipif(not pytest.config.getoption("--selenium"), reason="need --selenium to run")


@selenium_test
@pytest.mark.usefixtures("base_data_for_test_case")
@pytest.mark.usefixtures("test_download_dir")
@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
@pytest.mark.usefixtures("set_celery_always_eager")
class TestBulkEolCheckFunction(BaseSeleniumTest):
    def test_with_valid_query(self, browser, live_server, test_download_dir):
        # open the bulk eol check page
        browser.get(live_server + reverse("productdb:create-product_check"))

        # the page contains a text field, where the product IDs must be entered
        expected_text = "On this page, you can execute a bulk Product check of multiple Products against the local " \
                        "database. Please enter a list of Product IDs in the following text field separated by line " \
                        "breaks, e.g."
        page_text = browser.find_element_by_tag_name('body').text
        assert expected_text in page_text

        # enter the query and submit (whitespace is stripped)
        sample_eol_query = """WS-C2960-24LC-S
                    WS-C2960-24LC-S
                    WS-C2960-24LC-S
        WS-C2960-24LC-S
        WS-C2960-24LT-L
                    WS-C2960-24PC-S

                    WS-C2960X-24PD-L

                    WS-C2960X-24PD-L
                    WS-C2960X-24PD-L
                    MOH
                    WS-C2960-48PST-S
        WS-C2960-24TC-L
        MOH
                    WS-C2960-24TC-S
                    WS-C2960-24TT-L"""
        browser.find_element_by_id("id_name").send_keys("Test")
        browser.find_element_by_id("id_input_product_ids").send_keys(sample_eol_query)
        browser.find_element_by_id("submit").click()

        # verify result within the product summary table
        expected_product_summary_row = "WS-C2960-24LC-S 4 End of Sale,\n" \
                                       "End of New Service Attachment Date,\n" \
                                       "End of SW Maintenance Releases Date,\n" \
                                       "End of Routine Failure Analysis Date No"
        expected_not_found_query = "MOH 2 Not found in Database --- --- --- ---"

        table = browser.find_element_by_id('product_check_table')
        rows = table.find_elements_by_tag_name('tr')

        assert expected_product_summary_row in [row.text for row in rows]
        assert expected_not_found_query in [row.text for row in rows]

        # scroll down
        text_element = browser.find_element_by_class_name("alert-warning")
        browser.execute_script("return arguments[0].scrollIntoView();", text_element)

        # view the Vendor Bulletin
        dt_buttons = browser.find_element_by_class_name("dt-buttons")
        dt_buttons.find_element_by_link_text("show additional columns").click()
        browser.find_element_by_link_text("Vendor Bulletin").click()

        # test CSV download of the result table
        dt_buttons.find_element_by_link_text("CSV").send_keys(Keys.ENTER)

        # The file should download automatically (firefox is configured this way)

        # verify that the file is a CSV formatted field (with ";" as delimiter)
        # verfiy that the first line contains a link (not the Bulletin number)
        file = os.path.join(test_download_dir, "product check - Test.csv")
        header_line = "\ufeffProduct ID;Amount;Lifecycle State;Replacement Product ID;Replacement suggested by;" \
                      "Part of Product List;Vendor Bulletin;LC auto-sync\n"
        with open(file, "r") as f:
            assert header_line == f.readline()
            assert "http://www.cisco.com/en/" in f.readline()
