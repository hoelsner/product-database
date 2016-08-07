import time
from django.core.urlresolvers import reverse
from tests.base.django_test_cases import DestructiveProductDbFunctionalTest


class ProductDatabaseHomepageView(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml', 'default_text_blocks.yaml']

    def test_product_group_view(self):
        """
        test the basic view
        """
        # navigate to the homepage
        self.browser.get(self.server_url + reverse("productdb:home"))
        self.browser.implicitly_wait(3)

        # go to the "All Product Groups" view
        self.browser.find_element_by_id("nav_browse").click()
        self.browser.find_element_by_id("nav_browse_all_product_groups").click()

        # verify page by page title
        self.assertIn("All Product Groups", self.browser.find_element_by_tag_name("body").text)

        # test table content
        expected_table_content = """Vendor\nName"""
        table_rows = [
            'Cisco Systems Catalyst 3850',
            'Cisco Systems Catalyst 2960X',
            'Cisco Systems Catalyst 2960',
            'Juniper Networks EX2200',
        ]

        table = self.browser.find_element_by_id('product_group_table')
        self.assertIn(expected_table_content, table.text)
        for r in table_rows:
            self.assertIn(r, table.text)

        # search product group by vendor column
        table_rows = [
            'Juniper Networks EX2200',
        ]

        self.browser.find_element_by_id("column_search_Vendor").send_keys("Juni")
        table = self.browser.find_element_by_id('product_group_table')
        self.assertIn(expected_table_content, table.text)
        for r in table_rows:
            self.assertIn(r, table.text)
        self.browser.find_element_by_id("column_search_Vendor").clear()

        # search product group by vendor column
        table_rows = [
            'Cisco Systems Catalyst 3850',
            'Cisco Systems Catalyst 2960X',
            'Cisco Systems Catalyst 2960',
        ]

        self.browser.find_element_by_id("column_search_Name").send_keys("yst")
        time.sleep(2)
        table = self.browser.find_element_by_id('product_group_table')
        self.assertIn(expected_table_content, table.text)
        for r in table_rows:
            self.assertIn(r, table.text)
        self.browser.find_element_by_id("column_search_Name").clear()
        time.sleep(2)

        # click on the "Catalyst 2960X" link
        self.browser.find_element_by_partial_link_text("Catalyst 2960X").click()

        # verify page title
        self.assertIn("Catalyst 2960X Product Group details", self.browser.find_element_by_tag_name("body").text)

        # verify table content
        expected_table_content = """Product ID\nDescription\nList Price Lifecycle State"""
        table_rows = [
            'C2960X-STACK',
            'CAB-ACE',
            'CAB-STK-E-0.5M',
        ]

        table = self.browser.find_element_by_id('product_table')
        self.assertIn(expected_table_content, table.text)
        for r in table_rows:
            self.assertIn(r, table.text)
            # search product group by vendor column

        table_rows = [
            'WS-C2960X-24PD-L',
            'WS-C2960X-24TD-L',
        ]

        self.browser.find_element_by_id("column_search_Description").send_keys("2 x")
        table = self.browser.find_element_by_id('product_table')
        self.assertIn(expected_table_content, table.text)
        for r in table_rows:
            self.assertIn(r, table.text)
        self.browser.find_element_by_id("column_search_Description").clear()
        time.sleep(2)

        # open detail page
        self.browser.find_element_by_partial_link_text("C2960X-STACK").click()

        # verify page by title
        self.assertIn("C2960X-STACK Product details", self.browser.find_element_by_tag_name("body").text)
