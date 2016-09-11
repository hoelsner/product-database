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
@pytest.mark.usefixtures("set_test_config_file")
class TestBulkEolCheckFunction(BaseSeleniumTest):
    def test_with_valid_query(self, browser, live_server, test_download_dir):
        # open the bulk eol check page
        browser.get(live_server + reverse("productdb:bulk_eol_check"))

        # the page contains a text field, where the product IDs must be entered
        expected_text = "On this page, you can execute a bulk check of multiple products against the local database. " \
                        "Please enter a list of product IDs in the following text field separated by line breaks"
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
        browser.find_element_by_id("db_query").send_keys(sample_eol_query)
        browser.find_element_by_id("submit").click()

        # verify result within the product summary table
        expected_product_summary_row = "WS-C2960-24LC-S Catalyst 2960 24 10/100 (8 PoE) + 2 T/SFP LAN Lite Image 4 " \
                                       "End of Sale\nEnd of New Service Attachment Date\nEnd of SW Maintenance " \
                                       "Releases Date\nEnd of Routine Failure Analysis Date"
        expected_not_found_query = "MOH 2 Not found in database"

        table = browser.find_element_by_id('product_summary_table')
        rows = table.find_elements_by_tag_name('tr')

        assert expected_product_summary_row in [row.text for row in rows]
        assert expected_not_found_query in [row.text for row in rows]

        # verify result
        expected_product_row = "WS-C2960-24LC-S 2013/01/31 2014/01/31 2015/01/31 2015/01/31 2015/01/31 2019/01/29 " \
                               "2019/01/31 EOL9449"
        not_expected_product_row = "WS-C2960X-24PD-L"
        table = browser.find_element_by_id('product_table')
        rows = table.find_elements_by_tag_name('tr')
        assert expected_product_row in [row.text for row in rows]
        assert not_expected_product_row not in table.text

        # verify result within the skipped query table
        invalid_query = "MOH Not found in database"
        valid_query_without_eol = "WS-C2960X-24PD-L no EoL announcement found"
        unexpected_element = "\nWS-C2960-24LC-S"
        filtered_element = "\nNot found in database\n"
        table = browser.find_element_by_id('skipped_queries_table')
        rows = table.find_elements_by_tag_name('tr')
        assert invalid_query in [row.text for row in rows]
        assert valid_query_without_eol in [row.text for row in rows]
        assert unexpected_element not in table.text
        assert filtered_element not in table.text

        # test CSV download within the detailed page
        # download product summary table
        dt_buttons = browser.find_element_by_xpath('//div[@id="product_summary_table_wrapper"]/div/div/div/'
                                                        'div[@class="dt-buttons btn-group"]')
        dt_buttons.find_element_by_link_text("CSV").click()

        # The file should download automatically (firefox is configured this way)

        # Verify that the file is a CSV formatted field (with ";" as delimiter)
        file = os.path.join(test_download_dir, "Bulk EoL check (product summary table).csv")
        with open(file, "r") as f:
            assert "\ufeffProduct ID;Description;Amount;Lifecycle State\n" == f.readline()

        # download detailed lifecycle state table
        dt_buttons = browser.find_element_by_xpath('//div[@id="product_table_wrapper"]/div/div/div/'
                                                        'div[@class="dt-buttons btn-group"]')
        dt_buttons.find_element_by_link_text("CSV").send_keys(Keys.ENTER)

        # The file should download automatically (firefox is configured this way)

        # Verify that the file is a CSV formatted field (with ";" as delimiter)
        file = os.path.join(test_download_dir, "Bulk EoL check (detailed lifecycle states).csv")
        with open(file, "r") as f:
            assert "\ufeffPID;EoL anno.;EoS;EoNewSA;EoSWM;EoRFA;EoSCR;EoVulnServ;EoSup;Link\n" == f.readline()

        # download skipped queries table
        dt_buttons = browser.find_element_by_xpath('//div[@id="skipped_queries_table_wrapper"]/div/div/div/'
                                                        'div[@class="dt-buttons btn-group"]')
        dt_buttons.find_element_by_link_text("CSV").send_keys(Keys.ENTER)

        # The file should download automatically (firefox is configured this way)

        # Verify that the file is a CSV formatted field (with ";" as delimiter)
        file = os.path.join(test_download_dir, "Bulk EoL check (queries and products which are not found).csv")
        with open(file, "r") as f:
            assert "\ufeffQuery/Product ID;result\n" == f.readline()

    def test_bulk_eol_check_with_invalid_query(self, browser, live_server):
        # a user hits the bulk EoL page
        browser.get(live_server + reverse("productdb:bulk_eol_check"))

        # the page contains a text field, where the product IDs must be entered
        expected_text = "On this page, you can execute a bulk check of multiple products against the local database. " \
                        "Please enter a list of product IDs in the following text field separated by line breaks"
        page_text = browser.find_element_by_tag_name('body').text
        assert expected_text in page_text

        # the user enters the test query into the field and submit the result
        # (whitespace is stripped)
        sample_eol_query = "invalid_query"
        browser.find_element_by_id("db_query").send_keys(sample_eol_query)
        browser.find_element_by_id("submit").click()

        # verify result within the product summary table
        expected_text = "Query returned no results."
        page_text = browser.find_element_by_tag_name('body').text
        assert expected_text in page_text
