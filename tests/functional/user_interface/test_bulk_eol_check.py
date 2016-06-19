from django.core.urlresolvers import reverse
from selenium.webdriver.common.keys import Keys

from tests.base.django_test_cases import DestructiveProductDbFunctionalTest
import os


class TestBulkEolCheckTool(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml', ]

    def test_with_valid_queries(self):
        # a user hits the bulk EoL page
        self.browser.get(self.server_url + reverse("productdb:bulk_eol_check"))
        self.browser.implicitly_wait(3)

        # he sees the bulk EoL products textarea, which contains the text to enter the
        # product IDs separated by a line break
        expected_text = "On this page, you can execute a bulk check of multiple products against the local database. " \
                        "Please enter a list of product IDs in the following text field separated by line breaks"
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn(expected_text, page_text)

        # the user enters the test query into the field and submit the result
        # (whitespace is stripped)
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
        self.browser.find_element_by_id("db_query").send_keys(sample_eol_query)
        self.browser.find_element_by_id("submit").click()

        # verify result within the product summary table
        expected_product_summary_row = "WS-C2960-24LC-S Catalyst 2960 24 10/100 (8 PoE) + 2 T/SFP LAN Lite Image 4 " \
                                       "End of Sale\nEnd of New Service Attachment Date\nEnd of SW Maintenance " \
                                       "Releases Date\nEnd of Routine Failure Analysis Date"
        expected_not_found_query = "MOH 2 Not found in database"

        table = self.browser.find_element_by_id('product_summary_table')
        rows = table.find_elements_by_tag_name('tr')
        self.assertIn(expected_product_summary_row,
                      [row.text for row in rows])
        self.assertIn(expected_not_found_query,
                      [row.text for row in rows])

        # verify result within the product table which contains the lifecycle information
        expected_product_row = "WS-C2960-24LC-S 2013/01/31 2014/01/31 2015/01/31 2015/01/31 2015/01/31 2019/01/29 " \
                               "2019/01/31 EOL9449"
        not_expected_product_row = "WS-C2960X-24PD-L"
        table = self.browser.find_element_by_id('product_table')
        rows = table.find_elements_by_tag_name('tr')
        self.assertIn(expected_product_row, [row.text for row in rows])
        self.assertNotIn(not_expected_product_row, table.text)

        # verify result within the skipped query table
        invalid_query = "MOH Not found in database"
        valid_query_without_eol = "WS-C2960X-24PD-L no EoL announcement found"
        unexpected_element = "\nWS-C2960-24LC-S"
        filtered_element = "\nNot found in database\n"
        table = self.browser.find_element_by_id('skipped_queries_table')
        rows = table.find_elements_by_tag_name('tr')
        self.assertIn(invalid_query, [row.text for row in rows])
        self.assertIn(valid_query_without_eol, [row.text for row in rows])
        self.assertNotIn(unexpected_element, table.text)
        self.assertNotIn(filtered_element, table.text)

        # test CSV download within the detailed page
        # download product summary table
        dt_buttons = self.browser.find_element_by_xpath('//div[@id="product_summary_table_wrapper"]/div/div/div/'
                                                        'div[@class="dt-buttons btn-group"]')
        dt_buttons.find_element_by_link_text("CSV").click()

        # The file should download automatically (firefox is configured this way)

        # Verify that the file is a CSV formatted field (with ";" as delimiter)
        file = os.path.join(self.download_dir, "Bulk EoL check (product summary table).csv")
        f = open(file, "r")
        self.assertEqual("\ufeffProduct ID;Description;Amount;Lifecycle State\n", f.readline())
        f.close()

        # download detailed lifecycle state table
        dt_buttons = self.browser.find_element_by_xpath('//div[@id="product_table_wrapper"]/div/div/div/'
                                                        'div[@class="dt-buttons btn-group"]')
        dt_buttons.find_element_by_link_text("CSV").send_keys(Keys.ENTER)

        # The file should download automatically (firefox is configured this way)

        # Verify that the file is a CSV formatted field (with ";" as delimiter)
        file = os.path.join(self.download_dir, "Bulk EoL check (detailed lifecycle states).csv")
        f = open(file, "r")
        self.assertEqual("\ufeffPID;EoL anno.;EoS;EoNewSA;EoSWM;EoRFA;EoSCR;EoVulnServ;EoSup;Link\n", f.readline())
        f.close()

        # download skipped queries table
        dt_buttons = self.browser.find_element_by_xpath('//div[@id="skipped_queries_table_wrapper"]/div/div/div/'
                                                        'div[@class="dt-buttons btn-group"]')
        dt_buttons.find_element_by_link_text("CSV").send_keys(Keys.ENTER)

        # The file should download automatically (firefox is configured this way)

        # Verify that the file is a CSV formatted field (with ";" as delimiter)
        file = os.path.join(self.download_dir, "Bulk EoL check (queries and products which are not found).csv")
        f = open(file, "r")
        self.assertEqual("\ufeffQuery/Product ID;result\n", f.readline())
        f.close()

    def test_invalid_entry(self):
        # a user hits the bulk EoL page
        self.browser.get(self.server_url + reverse("productdb:bulk_eol_check"))
        self.browser.implicitly_wait(3)

        # he sees the bulk EoL products textarea, which contains the text to enter the
        # product IDs separated by a line break
        expected_text = "On this page, you can execute a bulk check of multiple products against the local database. " \
                        "Please enter a list of product IDs in the following text field separated by line breaks"
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn(expected_text, page_text)

        # the user enters the test query into the field and submit the result
        # (whitespace is stripped)
        sample_eol_query = "invalid_query"
        self.browser.find_element_by_id("db_query").send_keys(sample_eol_query)
        self.browser.find_element_by_id("submit").click()

        # verify result within the product summary table
        expected_text = "Query returned no results."
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn(expected_text, page_text)
