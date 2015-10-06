"""
Test which are executed with an
"""
from tests.base.django_test_cases import DestructiveProductDbFunctionalTest
import time


class ProductDbTestsWithEmptyDb(DestructiveProductDbFunctionalTest):
    """
    Tests with an empty database, only default values exists
    """
    fixtures = ['default_vendors.yaml']

    def setUp(self):
        super().setUp()
        self.clean_db()

    def test_browse_products_by_product_list_without_a_list(self):
        # a user hits the browse product list url, but no product lists are created
        self.browser.get(self.server_url + "/productdb/browse/")

        # the user sees the message, that no product list was found in database
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Warning: No product list found in database.", page_text)
        time.sleep(2)

    def test_browse_products_by_vendor_without_a_product(self):
        # a user hits the browse product list url, but no product lists are created
        self.browser.get(self.server_url + "/productdb/vendor/")

        # the user sees the message, that no product list was found in database
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("No data available in table", page_text)
        time.sleep(2)
