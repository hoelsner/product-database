import time
from django.core.urlresolvers import reverse
from tests.base.django_test_cases import DestructiveProductDbFunctionalTest


class ProductListTest(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml']

    def test_product_list(self):
        add_button_xpath = "id('product_list_table_wrapper')/div[1]/div[2]/div/div/a[1]"
        edit_button_xpath = "id('product_list_table_wrapper')/div[1]/div[2]/div/div/a[2]"
        delete_button_xpath = "id('product_list_table_wrapper')/div[1]/div[2]/div/div/a[3]"

        test_pl_name = "Test Product List"
        test_pl_description = "A sample description for the Product List."
        test_pl_product_list_ids = "C2960X-STACK;CAB-ACE\nWS-C2960-24TT-L;WS-C2960-24TC-S"
        test_pl_product_list_id = "C2960X-STACK"

        # open the homepage
        self.browser.get(self.server_url + reverse("productdb:home"))
        self.browser.implicitly_wait(3)

        # go to product list view
        self.browser.find_element_by_id("nav_browse").click()
        self.browser.find_element_by_id("nav_browse_all_product_lists").click()

        # verify that the add, edit and delete button is not visible
        body = self.browser.find_element_by_tag_name("body").text

        self.assertNotIn("Add New", body)
        self.assertNotIn("Edit Selected", body)
        self.assertNotIn("Delete Selected", body)

        # login to the page as admin user
        self.browser.find_element_by_id("navbar_login").click()
        self.handle_login_dialog(self.ADMIN_USERNAME, self.ADMIN_PASSWORD, "All Product Lists")

        # verify that the add, edit and delete buttons are visible
        body = self.browser.find_element_by_tag_name("body").text
        self.assertIn("Add New", body)
        self.assertIn("Edit Selected", body)
        self.assertIn("Delete Selected", body)

        # create a new product list
        self.browser.find_element_by_xpath(add_button_xpath).click()
        body = self.browser.find_element_by_tag_name("body").text
        self.assertIn("Add Product List", body)

        self.browser.find_element_by_id("id_name").send_keys(test_pl_name)
        self.browser.find_element_by_id("id_description").send_keys(test_pl_description)
        self.browser.find_element_by_id("id_string_product_list").send_keys(test_pl_product_list_ids)

        self.browser.find_element_by_id("submit").click()
        body = self.browser.find_element_by_tag_name("body").text
        self.assertIn("All Product Lists", body)
        self.assertIn(test_pl_name, body)

        # view the newly created product list
        self.browser.find_element_by_link_text(test_pl_name).click()
        body = self.browser.find_element_by_tag_name("body").text

        self.assertIn(test_pl_name, body)
        self.assertIn(test_pl_description, body)
        self.assertIn(test_pl_product_list_id, body)
        self.assertIn("maintained by %s" % self.ADMIN_USERNAME, body)

        # go back to the product list overview
        self.browser.find_element_by_id("_back").click()

        # edit the new product list
        self.browser.find_element_by_xpath("id('product_list_table')/tbody/tr[1]/td[2]").click()
        time.sleep(1)
        self.browser.find_element_by_xpath(edit_button_xpath).click()

        self.browser.find_element_by_id("id_description").send_keys(" EDITED")
        test_pl_description += " EDITED"

        self.browser.find_element_by_id("submit").click()

        body = self.browser.find_element_by_tag_name("body").text
        self.assertIn(test_pl_description, body)

        # delete the new product list
        self.browser.find_element_by_xpath("id('product_list_table')/tbody/tr[1]/td[2]").click()
        time.sleep(1)
        self.browser.find_element_by_xpath(delete_button_xpath).click()

        body = self.browser.find_element_by_tag_name("body").text
        self.assertIn("Delete Product List", body)

        self.browser.find_element_by_name("really_delete").click()
        self.browser.find_element_by_id("submit").click()

        # verify that the product list is deleted
        body = self.browser.find_element_by_tag_name("body").text
        self.assertNotIn(test_pl_description, body)
        self.assertIn("Product List %s successfully deleted." % test_pl_name, body)
