"""
Test of the "view vendor lifecycle information" view
"""
from tests.base.django_test_cases import DestructiveProductDbFunctionalTest
from selenium.webdriver.support.ui import Select
import time


class TestLifecycleViewByVendor(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml']

    def test_view_lifecycle_information_by_vendor(self):
        # a user hits the browse product list url
        self.browser.get(self.server_url + "/productdb/lifecycle/")
        self.browser.implicitly_wait(3)
        default_vendor = "Cisco Systems"

        # the default vendor is selected
        pl_selection = self.browser.find_element_by_id("vendor_selection")
        self.assertIn(default_vendor, pl_selection.text)
        pl_selection = Select(pl_selection)

        # and the expected product is visible
        expected_product = "WS-C2960-24-S"
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn(expected_product, page_text)

        # there are some elements visible
        dt_wrapper = self.browser.find_element_by_id("product_table_info")
        self.assertRegex(dt_wrapper.text, 'Showing 1 to \d+ of \d+ entries')

        # enter a "WS-C2960" in the search text
        search = self.browser.find_element_by_xpath('//div[@class="dataTables_filter"]/label/input[@type="search"]')
        search.send_keys("WS-C2960")

        # there are less elements visible
        dt_wrapper = self.browser.find_element_by_id("product_table_info")
        self.assertRegex(dt_wrapper.text, ".*Showing 1 to \d+ of \d+ entries.*")

        # switch to Vendor "Juniper Networks"
        pl_selection.select_by_visible_text("Juniper Networks")
        time.sleep(2)
        self.browser.find_element_by_id("submit").click()
        time.sleep(2)

        # there is only one element visible
        dt_wrapper = self.browser.find_element_by_id("product_table_info")
        self.assertRegex(dt_wrapper.text, r".*Showing 1 to 1 of \d+ entries.*")

        # check expected product
        expected_product = "EX2200-24T-4G"
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn(expected_product, page_text)

    def test_search_function(self):
        # a user hits the browse product list url
        self.browser.get(self.server_url + "/productdb/lifecycle/")
        self.browser.implicitly_wait(3)

        # he enters a search term in the search box
        search_term = "WS-C2960-24L"
        search_xpath = '//div[@id="product_table_wrapper"]/div[@id="product_table_filter"]/label/input[@type="search"]'
        search = self.browser.find_element_by_xpath(search_xpath)
        search.send_keys(search_term)
        time.sleep(3)

        # the table performs the search function and a defined amount of rows is displayed
        expected_table_content = """Product ID End of Sale End of SW Maintenance End of Support
Product ID End of Sale End of SW Maintenance End of Support"""
        table_rows = [
            "WS-C2960-24LC-S 2014/01/31 2015/01/31 2019/01/31",
            "WS-C2960-24LT-L 2014/01/31 2015/01/31 2019/01/31",
            "WS-C2960-24LC-S-RF 2018/01/31 2019/01/31",
        ]

        table = self.browser.find_element_by_id('product_table')
        self.assertIn(expected_table_content, table.text)
        for r in table_rows:
            self.assertIn(r, table.text)
