import os
import time

from django.core.urlresolvers import reverse
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from tests.base.django_test_cases import DestructiveProductDbFunctionalTest


class ProductDatabaseHomepageView(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml']

    def test_browse_product_list_view(self):
        expected_content = "This database contains information about network equipment like routers and switches " \
                           "from multiple"

        # a user hits the homepage of the product db
        self.browser.get(self.server_url + "/productdb/")
        self.browser.implicitly_wait(3)

        # check that the user sees a table
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn(expected_content, page_text)


class NotificationMessage(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml']

    def test_add_notification_message(self):
        # go to the Product Database Homepage
        self.browser.get(self.server_url + reverse("productdb:home"))
        self.browser.implicitly_wait(3)

        self.browser.find_element_by_id("navbar_login").click()

        expected_homepage_text = "This database contains information about network equipment like routers and " \
                                 "switches from multiple vendors."
        self.handle_login_dialog(
            expected_content=expected_homepage_text,
            username=self.ADMIN_USERNAME,
            password=self.ADMIN_PASSWORD
        )

        # add a new notification message
        self.browser.find_element_by_id("navbar_admin").click()
        self.browser.find_element_by_id("navbar_admin_notification_message").click()

        self.assertIn(
            "Add Notification Message",
            self.browser.find_element_by_tag_name("body").text
        )

        # add content
        title = "My message title"
        summary_message = "summary message"
        detailed_message = "detailed message"
        self.browser.find_element_by_id("id_title").send_keys(title)
        self.browser.find_element_by_id("id_summary_message").send_keys(summary_message)
        self.browser.find_element_by_id("id_detailed_message").send_keys(detailed_message)
        self.browser.find_element_by_id("submit").click()

        # verify that the message is visible on the homepage
        self.assertIn(title, self.browser.find_element_by_tag_name("body").text)
        self.assertIn(summary_message, self.browser.find_element_by_tag_name("body").text)


class BrowseProductsByVendor(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml']

    def test_browse_products_view(self):
        expected_cisco_row = "C2960X-STACK Catalyst 2960-X FlexStack Plus Stacking Module 1195.00 USD"
        expected_juniper_row = "EX-SFP-1GE-LX SFP 1000Base-LX Gigabit Ethernet Optics, 1310nm for " \
                               "10km transmission on SMF 1000.00 USD"
        default_vendor = "Cisco Systems"

        # a user hits the browse product list url
        self.browser.get(self.server_url + reverse("productdb:browse_vendor_products"))
        self.browser.implicitly_wait(3)

        # check that the user sees a table
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Showing 1 to", page_text)

        # the user sees a selection field, where the value "Cisco Systems" is selected
        pl_selection = self.browser.find_element_by_id("vendor_selection")
        self.assertIn(default_vendor, pl_selection.text)
        pl_selection = Select(pl_selection)

        # the table has three buttons: Copy, CSV and a PDF
        dt_buttons = self.browser.find_element_by_class_name("dt-buttons")

        self.assertEqual("PDF", dt_buttons.find_element_by_link_text("PDF").text)
        self.assertEqual("Copy", dt_buttons.find_element_by_link_text("Copy").text)
        self.assertEqual("CSV", dt_buttons.find_element_by_link_text("CSV").text)

        # the table shows 10 entries from the list (below the table, there is a string "Showing 1 to 10 of \d+ entries"
        dt_wrapper = self.browser.find_element_by_id("product_table_info")
        self.assertRegex(dt_wrapper.text, r"Showing 1 to \d+ of \d+ entries")

        # the page reloads and the table contains now the element "C2960X-STACK" as the first element of the table
        table = self.browser.find_element_by_id('product_table')
        rows = table.find_elements_by_tag_name('tr')
        self.assertIn(expected_cisco_row,
                      [row.text for row in rows])

        # the user chooses the list named "Juniper Networks" and press the button "view product list"
        pl_selection.select_by_visible_text("Juniper Networks")
        self.browser.find_element_by_id("submit").send_keys(Keys.ENTER)

        # the page reloads and the table contains now the element "EX-SFP-1GE-LX" as the first element of the table
        table = self.browser.find_element_by_id('product_table')
        rows = table.find_elements_by_tag_name('tr')

        match = False
        for i in range(0, 3):
            match = (expected_juniper_row,
                     [row.text for row in rows])
            if match:
                break
            time.sleep(3)
        if not match:
            self.fail("Element not found")

    def test_browse_products_view_csv_export(self):
        # a user hits the browse product list url
        self.browser.get(self.server_url + reverse("productdb:browse_vendor_products"))
        self.browser.implicitly_wait(3)

        # the user sees a selection field, where the value "Cisco Systems" is selected
        vendor_name = "Cisco Systems"
        pl_selection = self.browser.find_element_by_id("vendor_selection")
        self.assertIn(vendor_name, pl_selection.text)

        # the user hits the button CSV
        dt_buttons = self.browser.find_element_by_class_name("dt-buttons")
        dt_buttons.find_element_by_link_text("CSV").click()

        # the file should download automatically (firefox is configured this way)

        # verify that the file is a CSV formatted field (with ";" as delimiter)
        file = os.path.join(self.download_dir, "export products - %s.csv" % vendor_name)
        f = open(file, "r+")
        self.assertEqual("\ufeffProduct ID;Description;List Price;Lifecycle State\n", f.readline())
        f.close()

    def test_search_function(self):
        # a user hits the browse product list url
        self.browser.get(self.server_url + reverse("productdb:browse_vendor_products"))
        self.browser.implicitly_wait(3)

        # he enters a search term in the search box
        search_term = "WS-C2960X-24P"
        search_xpath = '//div[@class="col-sm-4"]/div[@id="product_table_filter"]/label/input[@type="search"]'
        search = self.browser.find_element_by_xpath(search_xpath)
        search.send_keys(search_term)
        time.sleep(3)

        # the table performs the search function and a defined amount of rows is displayed
        expected_table_content = """Product ID\nDescription\nList Price Lifecycle State"""
        table_rows = [
            'WS-C2960X-24PD-L Catalyst 2960-X 24 GigE PoE 370W, 2 x 10G SFP+, LAN Base 4595.00 USD',
            'WS-C2960X-24PS-L Catalyst 2960-X 24 GigE PoE 370W, 4 x 1G SFP, LAN Base 3195.00 USD',
        ]

        table = self.browser.find_element_by_id('product_table')
        self.assertIn(expected_table_content, table.text)
        for r in table_rows:
            self.assertIn(r, table.text)
        search.clear()

        # search product by column
        self.browser.find_element_by_id("column_search_Product ID").send_keys("WS-C2960X-24P(D|S)-L")
        table = self.browser.find_element_by_id('product_table')
        self.assertIn(expected_table_content, table.text)
        for r in table_rows:
            self.assertIn(r, table.text)
        self.browser.find_element_by_id("column_search_Product ID").clear()

        # search description by column
        self.browser.find_element_by_id("column_search_Description").send_keys("(1|10)G SFP")
        table = self.browser.find_element_by_id('product_table')
        self.assertIn(expected_table_content, table.text)
        for r in table_rows:
            self.assertIn(r, table.text)
        self.browser.find_element_by_id("column_search_Description").clear()

        # search description by column
        self.browser.find_element_by_id("column_search_List Price").send_keys("3195")
        table = self.browser.find_element_by_id('product_table')
        self.assertIn(expected_table_content, table.text)
        self.assertIn(r[1], table.text)
        self.browser.find_element_by_id("column_search_List Price").clear()


class BrowseAllProducts(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml']

    def test_browse_all_products_view(self):
        expected_cisco_row = "Cisco Systems C2960X-STACK Catalyst 2960-X FlexStack Plus Stacking Module 1195.00 USD"
        expected_juniper_row = "Juniper Networks EX-SFP-1GE-LX SFP 1000Base-LX Gigabit Ethernet Optics, 1310nm for " \
                               "10km transmission on SMF 1000.00 USD"

        # a user hits the browse product list url
        self.browser.get(self.server_url + reverse("productdb:all_products"))
        self.browser.implicitly_wait(5)

        # check that the user sees a table
        time.sleep(5)
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Showing 1 to", page_text)

        # the table has three buttons: Copy, CSV and a PDF
        dt_buttons = self.browser.find_element_by_class_name("dt-buttons")

        self.assertEqual("PDF", dt_buttons.find_element_by_link_text("PDF").text)
        self.assertEqual("Copy", dt_buttons.find_element_by_link_text("Copy").text)
        self.assertEqual("CSV", dt_buttons.find_element_by_link_text("CSV").text)

        # the table shows 10 entries from the list (below the table, there is a string "Showing 1 to 10 of \d+ entries"
        dt_wrapper = self.browser.find_element_by_id("product_table_info")
        self.assertRegex(dt_wrapper.text, r"Showing 1 to \d+ of \d+ entries")

        # the page reloads and the table contains now the element "C2960X-STACK" as the first element of the table
        table = self.browser.find_element_by_id('product_table')
        rows = table.find_elements_by_tag_name('tr')
        self.assertIn(expected_cisco_row,
                      [row.text for row in rows])

        # the page reloads and the table contains now the element "EX-SFP-1GE-LX" as the first element of the table
        table = self.browser.find_element_by_id('product_table')
        rows = table.find_elements_by_tag_name('tr')

        match = False
        for i in range(0, 3):
            match = (expected_juniper_row,
                     [row.text for row in rows])
            if match:
                break
            time.sleep(3)
        if not match:
            self.fail("Element not found")

    def test_browse_all_products_view_csv_export(self):
        # a user hits the browse product list url
        self.browser.get(self.server_url + reverse("productdb:all_products"))
        self.browser.implicitly_wait(3)

        # the user hits the button CSV
        dt_buttons = self.browser.find_element_by_class_name("dt-buttons")
        dt_buttons.find_element_by_link_text("CSV").click()

        # the file should download automatically (firefox is configured this way)

        # verify that the file is a CSV formatted field (with ";" as delimiter)
        file = os.path.join(self.download_dir, "export products.csv")
        f = open(file, "r+")
        self.assertEqual("\ufeffVendor;Product ID;Description;List Price;Lifecycle State\n", f.readline())
        f.close()

    def test_search_function(self):
        # a user hits the browse product list url
        self.browser.get(self.server_url + reverse("productdb:all_products"))
        self.browser.implicitly_wait(3)

        # he enters a search term in the search box
        search_term = "WS-C2960X-24P"
        search_xpath = '//div[@class="col-sm-4"]/div[@id="product_table_filter"]/label/input[@type="search"]'
        search = self.browser.find_element_by_xpath(search_xpath)
        search.send_keys(search_term)
        time.sleep(3)

        # the table performs the search function and a defined amount of rows is displayed
        expected_table_content = """Vendor\nProduct ID\nDescription\nList Price Lifecycle State"""
        table_rows = [
            'WS-C2960X-24PD-L Catalyst 2960-X 24 GigE PoE 370W, 2 x 10G SFP+, LAN Base 4595.00 USD',
            'WS-C2960X-24PS-L Catalyst 2960-X 24 GigE PoE 370W, 4 x 1G SFP, LAN Base 3195.00 USD',
        ]

        table = self.browser.find_element_by_id('product_table')
        self.assertIn(expected_table_content, table.text)
        for r in table_rows:
            self.assertIn(r, table.text)

        search.clear()

        # search vendor by column
        self.browser.find_element_by_id("column_search_Vendor").send_keys("Cisco")
        table = self.browser.find_element_by_id('product_table')
        self.assertIn(expected_table_content, table.text)
        for r in table_rows:
            self.assertIn(r, table.text)
        self.browser.find_element_by_id("column_search_Vendor").clear()

        # search product by column
        self.browser.find_element_by_id("column_search_Product ID").send_keys("WS-C2960X-24P(D|S)-L")
        table = self.browser.find_element_by_id('product_table')
        self.assertIn(expected_table_content, table.text)
        for r in table_rows:
            self.assertIn(r, table.text)
        self.browser.find_element_by_id("column_search_Product ID").clear()

        # search description by column
        self.browser.find_element_by_id("column_search_Description").send_keys("(1|10)G SFP")
        table = self.browser.find_element_by_id('product_table')
        self.assertIn(expected_table_content, table.text)
        for r in table_rows:
            self.assertIn(r, table.text)
        self.browser.find_element_by_id("column_search_Description").clear()

        # search description by column
        self.browser.find_element_by_id("column_search_List Price").send_keys("3195")
        table = self.browser.find_element_by_id('product_table')
        self.assertIn(expected_table_content, table.text)
        self.assertIn(r[1], table.text)
        self.browser.find_element_by_id("column_search_List Price").clear()
