"""
Test suite for the selenium test cases
"""
import os
import pytest
import time
import re
from django.core.urlresolvers import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tests import BaseSeleniumTest

selenium_test = pytest.mark.skipif(not pytest.config.getoption("--selenium"),
                                   reason="need --selenium to run (implicit usage of the --online flag")


@selenium_test
class TestCommonFunctions(BaseSeleniumTest):
    def test_login_only_mode(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        # open the homepage
        browser.get(liveserver + reverse("productdb:home"))

        expected_homepage_text = "This database contains information about network equipment like routers and " \
                                 "switches from multiple vendors."
        assert expected_homepage_text in browser.find_element_by_tag_name("body").text

        # Login as superuser - verify, that the "continue without login" button is visible
        browser.find_element_by_id("navbar_login").click()
        time.sleep(3)

        expected_login_continue_text = "continue without login"
        assert expected_login_continue_text in browser.find_element_by_tag_name("body").text

        # login as superuser
        browser.find_element_by_id("username").send_keys(self.ADMIN_USERNAME)
        browser.find_element_by_id("password").send_keys(self.ADMIN_PASSWORD)
        browser.find_element_by_id("login_button").click()
        time.sleep(3)

        # change settings to login only mode and save settings
        browser.find_element_by_id("navbar_admin").click()
        browser.find_element_by_id("navbar_admin_settings").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Settings")

        browser.find_element_by_id("id_login_only_mode").click()
        browser.find_element_by_id("submit").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Settings saved successfully")

        # go to the Product Database Homepage - it must be visible
        browser.get(liveserver + reverse("productdb:home"))
        self.wait_for_text_to_be_displayed_in_body_tag(browser, expected_homepage_text)

        # create the product list for the test case
        test_pl_name = "LoginOnly Product List"
        test_pl_description = "A sample description for the Product List."
        test_pl_product_list_ids = "C2960X-STACK;CAB-ACE\nWS-C2960-24TT-L;WS-C2960-24TC-S"
        test_pl_product_list_id = "C2960X-STACK"

        browser.find_element_by_id("product_list_link").click()
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((
            By.XPATH,
            "id('product_list_table_wrapper')")
        ))

        browser.find_element_by_link_text("Add New").click()
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "id_name")))

        browser.find_element_by_id("id_name").send_keys(test_pl_name)
        browser.find_element_by_id("id_description").send_keys(test_pl_description)
        browser.find_element_by_id("id_string_product_list").send_keys(test_pl_product_list_ids)
        browser.find_element_by_id("submit").click()
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((
            By.XPATH,
            "id('product_list_table_wrapper')")
        ))

        # logout - the login screen is visible
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_logout").click()
        expected_login_text = "Please enter your credentials below."
        self.wait_for_text_to_be_displayed_in_body_tag(browser, expected_login_text)

        # go manually to the Product Database Homepage - you must be redirected to the login screen
        browser.get(liveserver + reverse("productdb:home"))
        self.wait_for_text_to_be_displayed_in_body_tag(browser, expected_login_text)

        # verify, that the "continue without login" button is not visible
        assert expected_login_continue_text not in browser.find_element_by_tag_name("body").text

        # the product list must be reachable, even when in login only mode
        pl = self.api_helper.get_product_list_by_name(liveserver, test_pl_name)
        browser.get(liveserver + reverse("productdb:share-product_list", kwargs={"product_list_id": pl["id"]}))

        # verify some basic attributes of the page
        body = browser.find_element_by_tag_name("body").text
        assert test_pl_name in body
        assert test_pl_description in body
        assert test_pl_product_list_id in body
        assert "maintained by %s" % self.ADMIN_DISPLAY_NAME in body
        assert "%s</a>" % test_pl_product_list_id not in body, \
            "Link to Product Details should not be available"

        # login as API user
        browser.get(liveserver + reverse("productdb:home"))
        browser.find_element_by_id("username").send_keys(self.API_USERNAME)
        browser.find_element_by_id("password").send_keys(self.API_PASSWORD)
        browser.find_element_by_id("login_button").click()
        time.sleep(3)

        # the Product Database Homepage must be visible
        assert expected_homepage_text in browser.find_element_by_tag_name("body").text

        # disable the login only mode
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_logout").click()

        browser.find_element_by_id("username").send_keys(self.ADMIN_USERNAME)
        browser.find_element_by_id("password").send_keys(self.ADMIN_PASSWORD)
        browser.find_element_by_id("login_button").click()
        time.sleep(3)

        browser.find_element_by_id("navbar_admin").click()
        browser.find_element_by_id("navbar_admin_settings").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Settings")

        assert "Settings" in browser.find_element_by_tag_name("body").text
        browser.find_element_by_id("id_login_only_mode").click()
        browser.find_element_by_id("submit").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Settings saved successfully")

        # delete the new product list
        browser.get(liveserver + reverse("productdb:list-product_lists"))
        browser.find_element_by_xpath("id('product_list_table')/tbody/tr[1]/td[2]").click()
        time.sleep(1)
        browser.find_element_by_xpath("id('product_list_table_wrapper')/div[1]/div[2]/div/div/a[3]").click()
        time.sleep(3)

        body = browser.find_element_by_tag_name("body").text
        assert "Delete Product List" in body

        browser.find_element_by_name("really_delete").click()
        browser.find_element_by_id("submit").click()
        time.sleep(3)

        # verify that the product list is deleted
        body = browser.find_element_by_tag_name("body").text
        assert test_pl_description not in body
        assert "Product List %s successfully deleted." % test_pl_name in body

        # end session
        self.logout_user(browser)

    def test_change_password(self, browser, liveserver):
        """
        test change password procedure with a different user (part of the selenium_tests fixture)
        """
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        # login as the default API user
        browser.get(liveserver + reverse("login"))

        browser.find_element_by_id("username").send_keys("testpasswordchange")
        browser.find_element_by_id("password").send_keys("api")
        browser.find_element_by_id("login_button").click()
        time.sleep(3)

        # go to the change password dialog
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_change_password").click()
        time.sleep(3)

        assert "Old password" in browser.find_element_by_tag_name("body").text

        # chang the password to api1234
        browser.find_element_by_id("id_old_password").send_keys("api")
        browser.find_element_by_id("id_new_password1").send_keys("api1234")
        browser.find_element_by_id("id_new_password2").send_keys("api1234")
        browser.find_element_by_id("submit").click()
        time.sleep(3)

        assert "Password change successful" in browser.find_element_by_tag_name("body").text

        # logout
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_logout").click()
        time.sleep(3)

        expected_login_text = "Please enter your credentials below."
        assert expected_login_text in browser.find_element_by_tag_name("body").text

        # login with new password
        browser.find_element_by_id("username").send_keys("testpasswordchange")
        browser.find_element_by_id("password").send_keys("api1234")
        browser.find_element_by_id("login_button").click()
        time.sleep(3)

        # the Product Database Homepage must be visible
        expected_text = "This database contains information about network equipment like routers and " \
                        "switches from multiple vendors."
        assert expected_text in browser.find_element_by_tag_name("body").text

        # end session
        self.logout_user(browser)


@selenium_test
class TestUserProfile(BaseSeleniumTest):
    def test_preferred_vendor_user_profile(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        browser.get(liveserver + reverse("productdb:home"))

        # verify the vendor selection if the user is not logged in
        browser.find_element_by_id("nav_browse").click()
        browser.find_element_by_id("nav_browse_all_vendor_products").click()
        assert "Browse Products by Vendor" in browser.find_element_by_class_name("page-header").text, \
            "Should view the Browse Product by Vendor page"

        # login
        browser.find_element_by_id("navbar_login").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Please enter your credentials below.")

        homepage_message = "Browse Products by Vendor"
        self.login_user(browser, self.API_USERNAME, self.API_PASSWORD, homepage_message)

        # verify the selected default vendor
        pref_vendor_select = browser.find_element_by_id("vendor_selection")
        assert "Cisco Systems" in pref_vendor_select.text, "selected by default"

        # view the edit settings page
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_user_profile").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Edit User Profile")

        # verify that the vendor with the ID 1 is selected
        pref_vendor_select = browser.find_element_by_id("id_preferred_vendor")
        assert "Cisco Systems" in pref_vendor_select.text
        pref_vendor_select = Select(pref_vendor_select)

        # change the vendor selection
        changed_vendor_name = "Juniper Networks"
        pref_vendor_select.select_by_visible_text(changed_vendor_name)
        browser.find_element_by_id("submit").send_keys(Keys.ENTER)

        # redirect to the Browse Products by Vendor
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Browse Products by Vendor")

        # verify that the new default vendor is selected
        pref_vendor_select = browser.find_element_by_id("vendor_selection")
        assert changed_vendor_name in pref_vendor_select.text

        # end session
        self.logout_user(browser)

    def test_email_change_in_user_profile(self, browser, liveserver):
        """
        use separate user from the selenium_tests fixture
        """
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)
        browser.get(liveserver + reverse("productdb:home"))

        # login
        browser.find_element_by_id("navbar_login").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Please enter your credentials below.")

        homepage_message = "This database contains information about network equipment like routers and switches " \
                           "from multiple vendors."
        self.login_user(browser, "testuserprofilemail", self.API_PASSWORD, homepage_message)

        # view the edit settings page
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_user_profile").click()
        assert "api@localhost.localhost" in browser.find_element_by_id("id_email").get_attribute('value')

        # change email
        new_email = "a@b.com"
        browser.find_element_by_id("id_email").clear()
        browser.find_element_by_id("id_email").send_keys(new_email)
        browser.find_element_by_id("submit").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, homepage_message)

        # verify redirect to homepage
        assert "User Profile successful updated" in browser.find_element_by_tag_name("body").text, \
            "Should view a message that the user profile was saved"

        # verify new value in email address
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_user_profile").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Edit User Profile")

        assert new_email in browser.find_element_by_id("id_email").get_attribute('value'), \
            "Show view the correct email address of the user (%s)" % new_email

        # end session
        self.logout_user(browser)

    def test_search_option_in_user_profile(self, browser, liveserver):
        """
        use separate user from the selenium_tests fixture
        """
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        search_term = "WS-C2960X-24T(D|S)"
        browser.get(liveserver + reverse("productdb:home"))

        # login
        homepage_message = "This database contains information about network equipment like routers and switches " \
                           "from multiple vendors."
        browser.find_element_by_id("navbar_login").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Please enter your credentials below.")
        self.login_user(browser, "testregexsession", self.API_PASSWORD, homepage_message)

        # go to the all products view
        expected_content = "On this page, you can view all products that are stored in the database."

        browser.find_element_by_id("nav_browse").click()
        browser.find_element_by_id("nav_browse_all_products").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, expected_content)

        # try to search for the product
        browser.find_element_by_id("column_search_Product ID").send_keys(search_term)

        self.wait_for_text_to_be_displayed_in_body_tag(browser, "No matching records found")

        # enable the regular expression search feature in the user profile
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_user_profile").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Contact eMail:")

        expected_content = "On this page, you can view all products that are stored in the database."
        browser.find_element_by_id("id_regex_search").click()
        browser.find_element_by_id("submit").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, expected_content)

        browser.find_element_by_id("column_search_Product ID").send_keys(search_term)
        time.sleep(3)

        assert "WS-C2960X-24TS" in browser.find_element_by_tag_name("body").text, \
            "Should show no results (regular expression is used but by default not enabled)"

        assert "WS-C2960X-24TD" in browser.find_element_by_tag_name("body").text, \
            "Should show no results (regular expression is used but by default not enabled)"

        # end session
        self.logout_user(browser)


@selenium_test
class TestProductLists(BaseSeleniumTest):
    def test_product_list(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        add_button_xpath = "id('product_list_table_wrapper')/div[1]/div[2]/div/div/a[1]"
        edit_button_xpath = "id('product_list_table_wrapper')/div[1]/div[2]/div/div/a[2]"
        delete_button_xpath = "id('product_list_table_wrapper')/div[1]/div[2]/div/div/a[3]"

        test_pl_name = "Test Product List"
        test_pl_description = "A sample description for the Product List."
        test_pl_product_list_ids = "C2960X-STACK;CAB-ACE\nWS-C2960-24TT-L;WS-C2960-24TC-S"
        test_pl_product_list_id = "C2960X-STACK"

        # open the homepage
        browser.get(liveserver + reverse("productdb:home"))

        # go to product list view
        browser.find_element_by_id("nav_browse").click()
        browser.find_element_by_id("nav_browse_all_product_lists").click()
        time.sleep(3)

        # verify that the add, edit and delete button is not visible
        body = browser.find_element_by_tag_name("body").text

        assert "Add New" not in body
        assert "Edit Selected" not in body
        assert "Delete Selected" not in body

        # login to the page as admin user
        browser.find_element_by_id("navbar_login").click()
        time.sleep(3)

        self.login_user(browser, self.ADMIN_USERNAME, self.ADMIN_PASSWORD, "All Product Lists")

        # verify that the add, edit and delete buttons are visible
        body = browser.find_element_by_tag_name("body").text
        assert "Add New" in body
        assert "Edit Selected" in body
        assert "Delete Selected" in body

        # create a new product list
        browser.find_element_by_xpath(add_button_xpath).click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Add Product List")

        browser.find_element_by_id("id_name").send_keys(test_pl_name)
        browser.find_element_by_id("id_description").send_keys(test_pl_description)
        browser.find_element_by_id("id_string_product_list").send_keys(test_pl_product_list_ids)

        browser.find_element_by_id("submit").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "All Product Lists")
        assert test_pl_name in browser.find_element_by_tag_name("body").text

        # view the newly created product list
        browser.find_element_by_link_text(test_pl_name).click()
        time.sleep(3)

        body = browser.find_element_by_tag_name("body").text
        assert test_pl_name in body
        assert test_pl_description in body
        assert test_pl_product_list_id in body
        assert "maintained by %s" % self.ADMIN_DISPLAY_NAME in body
        assert browser.find_element_by_link_text(test_pl_product_list_id) is not None, \
            "Link to Product Details should be available"

        # go back to the product list overview
        browser.find_element_by_id("_back").click()

        # edit the new product list
        browser.find_element_by_xpath("id('product_list_table')/tbody/tr[1]/td[2]").click()
        time.sleep(3)
        browser.find_element_by_xpath(edit_button_xpath).click()
        time.sleep(3)

        browser.find_element_by_id("id_description").send_keys(" EDITED")
        test_pl_description += " EDITED"

        browser.find_element_by_id("submit").click()
        time.sleep(3)

        body = browser.find_element_by_tag_name("body").text
        assert test_pl_description in body

        # delete the new product list
        browser.find_element_by_xpath("id('product_list_table')/tbody/tr[1]/td[2]").click()
        time.sleep(1)
        browser.find_element_by_xpath(delete_button_xpath).click()
        time.sleep(3)

        body = browser.find_element_by_tag_name("body").text
        assert "Delete Product List" in body

        browser.find_element_by_name("really_delete").click()
        browser.find_element_by_id("submit").click()
        time.sleep(3)

        # verify that the product list is deleted
        body = browser.find_element_by_tag_name("body").text
        assert test_pl_description not in body
        assert "Product List %s successfully deleted." % test_pl_name in body


@selenium_test
class TestProductDatabaseViews(BaseSeleniumTest):
    def test_search_on_homepage(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        # navigate to the homepage
        browser.get(liveserver + reverse("productdb:home"))

        browser.find_element_by_id("search_text_field").send_keys("WS-C2960X-24")
        browser.find_element_by_id("submit_search").click()

        # verify page by page title
        assert "All Products" in browser.find_element_by_tag_name("body").text
        time.sleep(2)

        # test table content
        expected_table_content = """Vendor Product ID Description List Price Lifecycle State"""
        contain_table_rows = [
            "Cisco Systems WS-C2960X-24PD-L Catalyst 2960-X 24 GigE PoE 370W, 2 x 10G SFP+, LAN Base 4595.00 USD",
            "Cisco Systems WS-C2960X-24PS-L Catalyst 2960-X 24 GigE PoE 370W, 4 x 1G SFP, LAN Base 3195.00 USD",
        ]
        not_contain_table_rows = [
            "Juniper Networks"
        ]

        table = browser.find_element_by_id('product_table')
        assert expected_table_content in table.text

        for r in contain_table_rows:
            assert r in table.text

        for r in not_contain_table_rows:
            assert r not in table.text

    def test_product_group_view(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        # navigate to the homepage
        browser.get(liveserver + reverse("productdb:home"))

        # go to the "All Product Groups" view
        browser.find_element_by_id("nav_browse").click()
        browser.find_element_by_id("nav_browse_all_product_groups").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "All Product Groups")

        # test table content
        expected_table_content = """Vendor\nName"""
        table_rows = [
            'Cisco Systems Catalyst 3850',
            'Cisco Systems Catalyst 2960X',
            'Cisco Systems Catalyst 2960',
            'Juniper Networks EX2200',
        ]

        table = browser.find_element_by_id('product_group_table')
        self.wait_for_text_to_be_displayed_in_body_tag(browser, expected_table_content)
        for r in table_rows:
            assert r in table.text

        # search product group by vendor column
        table_rows = [
            'Juniper Networks EX2200',
        ]

        browser.find_element_by_id("column_search_Vendor").send_keys("Juni")
        table = browser.find_element_by_id('product_group_table')
        assert expected_table_content in table.text
        for r in table_rows:
            assert r in table.text
        browser.find_element_by_id("column_search_Vendor").clear()

        # search product group by vendor column
        table_rows = [
            'Cisco Systems Catalyst 3850',
            'Cisco Systems Catalyst 2960X',
            'Cisco Systems Catalyst 2960',
        ]

        browser.find_element_by_id("column_search_Name").send_keys("yst")
        time.sleep(2)
        table = browser.find_element_by_id('product_group_table')
        assert expected_table_content in table.text
        for r in table_rows:
            assert r in table.text
        browser.find_element_by_id("column_search_Name").clear()
        time.sleep(2)

        # click on the "Catalyst 2960X" link
        browser.find_element_by_partial_link_text("Catalyst 2960X").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Catalyst 2960X Product Group details")

        # verify table content
        expected_table_content = """Product ID\nDescription\nList Price Lifecycle State"""
        table_rows = [
            'C2960X-STACK',
            'CAB-ACE',
            'CAB-STK-E-0.5M',
        ]

        table = browser.find_element_by_id('product_table')
        assert expected_table_content in table.text
        for r in table_rows:
            assert r in table.text
            # search product group by vendor column

        table_rows = [
            'WS-C2960X-24PD-L',
            'WS-C2960X-24TD-L',
        ]

        browser.find_element_by_id("column_search_Description").send_keys("2 x")
        table = browser.find_element_by_id('product_table')
        assert expected_table_content in table.text
        for r in table_rows:
            assert r in table.text
        browser.find_element_by_id("column_search_Description").clear()
        time.sleep(2)

        # open detail page
        browser.find_element_by_partial_link_text("C2960X-STACK").click()
        detail_link = browser.current_url
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "C2960X-STACK Product details")

        # verify that the "Internal Product ID" is not visible (because not set)
        assert "Internal Product ID" not in browser.find_element_by_tag_name("body").text

        # add an internal product ID and verify that it is visible
        test_internal_product_id = "123456789-abcdef"
        p = self.api_helper.update_product(liveserver_url=liveserver, product_id="C2960X-STACK",
                                           internal_product_id=test_internal_product_id)

        browser.get(liveserver + reverse("productdb:product-detail", kwargs={"product_id": p["id"]}))
        page_text = browser.find_element_by_tag_name("body").text
        assert "Internal Product ID" in page_text
        assert test_internal_product_id in page_text

        # end session
        self.logout_user(browser)

    def test_add_notification_message(self, browser, liveserver):
        # go to the Product Database Homepage
        browser.get(liveserver + reverse("productdb:home"))
        browser.find_element_by_id("navbar_login").click()
        time.sleep(3)

        expected_homepage_text = "This database contains information about network equipment like routers and " \
                                 "switches from multiple vendors."
        self.login_user(
            browser,
            expected_content=expected_homepage_text,
            username=self.ADMIN_USERNAME,
            password=self.ADMIN_PASSWORD
        )

        # add a new notification message
        browser.find_element_by_id("navbar_admin").click()
        browser.find_element_by_id("navbar_admin_notification_message").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Add Notification Message")

        # add content
        title = "My message title"
        summary_message = "summary message"
        detailed_message = "detailed message"
        browser.find_element_by_id("id_title").send_keys(title)
        browser.find_element_by_id("id_summary_message").send_keys(summary_message)
        browser.find_element_by_id("id_detailed_message").send_keys(detailed_message)
        browser.find_element_by_id("submit").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, title)

        assert summary_message in browser.find_element_by_tag_name("body").text

        # end session
        self.logout_user(browser)

    def test_browse_products_view(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        expected_cisco_row = "C2960X-STACK Catalyst 2960-X FlexStack Plus Stacking Module 1195.00 USD"
        expected_juniper_row = "EX-SFP-1GE-LX SFP 1000Base-LX Gigabit Ethernet Optics, 1310nm for " \
                               "10km transmission on SMF 1000.00 USD"
        default_vendor = "Cisco Systems"

        # a user hits the browse product list url
        browser.get(liveserver + reverse("productdb:browse_vendor_products"))
        time.sleep(5)

        # check that the user sees a table
        page_text = browser.find_element_by_tag_name('body').text
        assert "Showing 1 to" in page_text

        # the user sees a selection field, where the value "Cisco Systems" is selected
        pl_selection = browser.find_element_by_id("vendor_selection")
        assert default_vendor in pl_selection.text

        # the table has three buttons: Copy, CSV and a PDF
        dt_buttons = browser.find_element_by_class_name("dt-buttons")

        assert "PDF" == dt_buttons.find_element_by_link_text("PDF").text
        assert "Copy" == dt_buttons.find_element_by_link_text("Copy").text
        assert "CSV" == dt_buttons.find_element_by_link_text("CSV").text
        assert "Excel" == dt_buttons.find_element_by_link_text("Excel").text

        # the table shows 10 entries from the list (below the table, there is a string "Showing 1 to 10 of \d+ entries"
        dt_wrapper = browser.find_element_by_id("product_table_info")
        assert re.match(r"Showing 1 to \d+ of \d+ entries", dt_wrapper.text) is not None

        # the page reloads and the table contains now the element "C2960X-STACK" as the first element of the table
        table = browser.find_element_by_id('product_table')
        rows = table.find_elements_by_tag_name('tr')
        assert expected_cisco_row in [row.text for row in rows]

        # navigate to a detail view
        link = browser.find_element_by_link_text("PWR-C1-350WAC")
        browser.execute_script("return arguments[0].scrollIntoView();", link)
        time.sleep(1)
        test_product_id = "WS-C2960-24LT-L"
        browser.find_element_by_link_text(test_product_id).click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "%s Product details" % test_product_id)

        # reopen the browse vendor products table
        browser.get(liveserver + reverse("productdb:browse_vendor_products"))
        time.sleep(5)

        # the user sees a selection field, where the value "Cisco Systems" is selected
        pl_selection = browser.find_element_by_id("vendor_selection")
        assert default_vendor in pl_selection.text
        pl_selection = Select(pl_selection)

        # the user chooses the list named "Juniper Networks" and press the button "view product list"
        pl_selection.select_by_visible_text("Juniper Networks")
        browser.find_element_by_id("submit").send_keys(Keys.ENTER)
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "EX-SFP-1GE-LX")

        # the page reloads and the table contains now the element "EX-SFP-1GE-LX" as the first element of the table
        table = browser.find_element_by_id('product_table')
        rows = table.find_elements_by_tag_name('tr')

        match = False
        for i in range(0, 3):
            match = (expected_juniper_row, [row.text for row in rows])
            if match:
                break
            time.sleep(3)
        if not match:
            pytest.fail("Element not found")

    def test_browse_products_view_csv_export(self, browser, liveserver, test_download_dir):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        # a user hits the browse product list url
        browser.get(liveserver + reverse("productdb:browse_vendor_products"))

        # the user sees a selection field, where the value "Cisco Systems" is selected
        vendor_name = "Cisco Systems"
        pl_selection = browser.find_element_by_id("vendor_selection")
        assert vendor_name in pl_selection.text

        # the user hits the button CSV
        dt_buttons = browser.find_element_by_class_name("dt-buttons")
        dt_buttons.find_element_by_link_text("CSV").click()

        # the file should download automatically (firefox is configured this way)
        time.sleep(2)

        # verify that the file is a CSV formatted field (with ";" as delimiter)
        file = os.path.join(test_download_dir, "export products - %s.csv" % vendor_name)
        with open(file, "r+", encoding="utf-8") as f:
            assert "Product ID;Description;List Price;Lifecycle State\n" == f.readline()

    def test_search_function_on_browse_vendor_products_view(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        # a user hits the browse product list url
        browser.get(liveserver + reverse("productdb:browse_vendor_products"))
        time.sleep(5)

        # he enters a search term in the search box
        search_term = "WS-C2960X-24P"
        search_xpath = '//div[@class="col-sm-4"]/div[@id="product_table_filter"]/label/input[@type="search"]'
        search = browser.find_element_by_xpath(search_xpath)
        search.send_keys(search_term)
        time.sleep(3)

        # show product groups
        dt_buttons = browser.find_element_by_class_name("dt-buttons")
        dt_buttons.find_element_by_link_text("show additional columns").click()
        browser.find_element_by_link_text("Internal Product ID").click()
        browser.find_element_by_link_text("Product Group").click()

        # the table performs the search function and a defined amount of rows is displayed
        expected_table_content = "Product ID Product Group Description " \
                                 "List Price Lifecycle State Internal Product ID"
        table_rows = [
            "WS-C2960X-24PD-L Catalyst 2960X Catalyst 2960-X 24 GigE PoE 370W, 2 x 10G SFP+, "
            "LAN Base 4595.00 USD 2960x-24pd-l",
            "WS-C2960X-24PS-L Catalyst 2960X Catalyst 2960-X 24 GigE PoE 370W, 4 x 1G SFP, "
            "LAN Base 3195.00 USD 2960x-24ps-l"
        ]

        table = browser.find_element_by_id('product_table')
        assert expected_table_content in table.text
        for r in table_rows:
            assert r in table.text
        browser.find_element_by_xpath(search_xpath).clear()
        time.sleep(1)

        # search product by column (contains)
        browser.find_element_by_id("column_search_Product ID").send_keys("WS-C2960X-24P")
        time.sleep(2)
        table = browser.find_element_by_id('product_table')
        assert expected_table_content in table.text
        for r in table_rows:
            assert r in table.text

        browser.find_element_by_id("column_search_Product ID").clear()

        # search product by column (contains)
        browser.find_element_by_id("column_search_Product Group").send_keys("2960X")
        time.sleep(2)
        table = browser.find_element_by_id('product_table')
        assert expected_table_content in table.text
        for r in table_rows:
            assert r in table.text

        browser.find_element_by_id("column_search_Product Group").clear()

        # search description by column
        browser.find_element_by_id("column_search_Description").send_keys("10G SFP")
        time.sleep(2)
        table = browser.find_element_by_id('product_table')
        assert expected_table_content in table.text
        assert table_rows[0] in table.text
        browser.find_element_by_id("column_search_Description").clear()

        # search description by column
        browser.find_element_by_id("column_search_List Price").send_keys("3195")
        time.sleep(2)
        table = browser.find_element_by_id('product_table')
        assert expected_table_content in table.text
        assert r[1] in table.text
        browser.find_element_by_id("column_search_List Price").clear()

    def test_browse_all_products_view(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        expected_cisco_row = "Cisco Systems C2960X-STACK Catalyst 2960-X FlexStack Plus Stacking Module 1195.00 USD"
        expected_juniper_row = "Juniper Networks EX-SFP-1GE-LX SFP 1000Base-LX Gigabit Ethernet Optics, 1310nm for " \
                               "10km transmission on SMF 1000.00 USD"

        # a user hits the browse product list url
        browser.get(liveserver + reverse("productdb:all_products"))

        # check that the user sees a table
        time.sleep(5)
        page_text = browser.find_element_by_tag_name('body').text
        assert "Showing 1 to" in page_text

        # the table has three buttons: Copy, CSV and a PDF
        dt_buttons = browser.find_element_by_class_name("dt-buttons")

        assert "PDF" == dt_buttons.find_element_by_link_text("PDF").text
        assert "Copy" == dt_buttons.find_element_by_link_text("Copy").text
        assert "CSV" == dt_buttons.find_element_by_link_text("CSV").text
        assert "Excel" == dt_buttons.find_element_by_link_text("Excel").text

        # the table shows 10 entries from the list (below the table, there is a string "Showing 1 to 10 of \d+ entries"
        dt_wrapper = browser.find_element_by_id("product_table_info")
        assert re.match(r"Showing 1 to \d+ of \d+ entries", dt_wrapper.text) is not None

        # the page reloads and the table contains now the element "C2960X-STACK" as the first element of the table
        table = browser.find_element_by_id('product_table')
        rows = table.find_elements_by_tag_name('tr')
        assert expected_cisco_row in [row.text for row in rows]

        # the page reloads and the table contains now the element "EX-SFP-1GE-LX" as the first element of the table
        table = browser.find_element_by_id('product_table')
        rows = table.find_elements_by_tag_name('tr')

        match = False
        for i in range(0, 3):
            match = (expected_juniper_row,
                     [row.text for row in rows])
            if match:
                break
            time.sleep(3)
        if not match:
            pytest.fail("Element not found")

        # navigate to a detail view
        test_product_id = "GLC-LH-SMD="
        browser.find_element_by_link_text(test_product_id).click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "%s Product details" % test_product_id)

    def test_browse_all_products_view_csv_export(self, browser, liveserver, test_download_dir):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        # a user hits the browse product list url
        browser.get(liveserver + reverse("productdb:all_products"))

        # the user hits the button CSV
        dt_buttons = browser.find_element_by_class_name("dt-buttons")
        dt_buttons.find_element_by_link_text("CSV").click()

        # the file should download automatically (firefox is configured this way)
        time.sleep(2)

        # verify that the file is a CSV formatted field (with ";" as delimiter)
        file = os.path.join(test_download_dir, "export products.csv")
        with open(file, "r+", encoding="utf-8") as f:
            assert "Vendor;Product ID;Description;List Price;Lifecycle State\n" == f.readline()

    def test_search_function_on_all_products_view(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        # a user hits the browse product list url
        browser.get(liveserver + reverse("productdb:all_products"))

        # he enters a search term in the search box
        search_term = "WS-C2960X-24P"
        search_xpath = '//div[@class="col-sm-4"]/div[@id="product_table_filter"]/label/input[@type="search"]'
        search = browser.find_element_by_xpath(search_xpath)
        search.send_keys(search_term)
        time.sleep(3)

        # the table performs the search function and a defined amount of rows is displayed
        expected_table_content = """Vendor Product ID Description List Price Lifecycle State"""
        table_rows = [
            'WS-C2960X-24PD-L Catalyst 2960-X 24 GigE PoE 370W, 2 x 10G SFP+, LAN Base 4595.00 USD',
            'WS-C2960X-24PS-L Catalyst 2960-X 24 GigE PoE 370W, 4 x 1G SFP, LAN Base 3195.00 USD',
        ]

        table = browser.find_element_by_id('product_table')
        assert expected_table_content in table.text
        for r in table_rows:
            assert r in table.text

        browser.find_element_by_xpath(search_xpath).clear()
        time.sleep(1)

        # search vendor by column
        browser.find_element_by_id("column_search_Vendor").send_keys("Cisco")
        time.sleep(2)
        table = browser.find_element_by_id('product_table')
        assert expected_table_content in table.text
        for r in table_rows:
            assert r in table.text
        browser.find_element_by_id("column_search_Vendor").clear()

        # search product by column
        browser.find_element_by_id("column_search_Product ID").send_keys("WS-C2960X-24P")
        time.sleep(2)
        table = browser.find_element_by_id('product_table')
        assert expected_table_content in table.text
        for r in table_rows:
            assert r in table.text
        browser.find_element_by_id("column_search_Product ID").clear()

        # search description by column
        browser.find_element_by_id("column_search_Description").send_keys("10G SFP")
        time.sleep(2)
        table = browser.find_element_by_id('product_table')
        assert expected_table_content in table.text
        assert table_rows[0] in table.text
        browser.find_element_by_id("column_search_Description").clear()

        # search description by column
        browser.find_element_by_id("column_search_List Price").send_keys("3195")
        time.sleep(2)
        table = browser.find_element_by_id('product_table')
        assert expected_table_content in table.text
        assert r[1] in table.text
        browser.find_element_by_id("column_search_List Price").clear()
