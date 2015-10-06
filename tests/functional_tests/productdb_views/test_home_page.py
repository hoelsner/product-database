"""
Basic tests for the homepage view (just to make sure that there is no issue with the template)
"""
from tests.base.django_test_cases import DestructiveProductDbFunctionalTest


class ProductDatabaseHomepageView(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml']

    def test_browse_product_list_view(self):
        expected_content = "This service provides a central point of management for product information about " \
                           "network equipment. It also provides import, synchronization and crawling functions for " \
                           "certain information from vendors."

        # a user hits the homepage of the product db
        self.browser.get(self.server_url + "/productdb/")
        self.browser.implicitly_wait(3)

        # check that the user sees a table
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn(expected_content, page_text)
