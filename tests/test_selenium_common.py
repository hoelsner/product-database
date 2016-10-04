"""
Test suite for the selenium test cases
"""
import os
import pytest
import time
import re
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from mixer.backend.django import mixer
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select

from app.config.settings import AppSettings
from app.productdb.models import Vendor, Product
from tests import BaseSeleniumTest

pytestmark = pytest.mark.django_db
selenium_test = pytest.mark.skipif(not pytest.config.getoption("--selenium"), reason="need --selenium to run")


@pytest.mark.usefixtures("base_data_for_test_case")
@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
@pytest.mark.usefixtures("import_default_text_blocks")
@pytest.mark.usefixtures("set_test_config_file")
@selenium_test
class TestCommonFunctions(BaseSeleniumTest):
    @pytest.mark.usefixtures("mock_cisco_eox_api_access_available")
    def test_login_only_mode(self, browser, live_server):
        # open the homepage
        browser.get(live_server + reverse("productdb:home"))

        expected_homepage_text = "This database contains information about network equipment like routers and " \
                                 "switches from multiple vendors."
        assert expected_homepage_text in browser.find_element_by_tag_name("body").text

        # Login as superuser - verify, that the "continue without login" button is visible
        browser.find_element_by_id("navbar_login").click()

        expected_login_continue_text = "continue without login"
        assert expected_login_continue_text in browser.find_element_by_tag_name("body").text

        # login as superuser
        browser.find_element_by_id("username").send_keys(self.ADMIN_USERNAME)
        browser.find_element_by_id("password").send_keys(self.ADMIN_PASSWORD)
        browser.find_element_by_id("login_button").click()

        # change settings to login only mode and save settings
        browser.find_element_by_id("navbar_admin").click()
        browser.find_element_by_id("navbar_admin_settings").click()
        assert "Settings" in browser.find_element_by_tag_name("body").text
        browser.find_element_by_id("id_login_only_mode").click()
        browser.find_element_by_id("submit").click()
        assert "Settings saved successfully" in browser.find_element_by_tag_name("body").text

        # go to the Product Database Homepage - it must be visible
        browser.get(live_server + reverse("productdb:home"))
        assert expected_homepage_text in browser.find_element_by_tag_name("body").text

        # logout - the login screen is visible
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_logout").click()
        expected_login_text = "Please enter your credentials below."
        assert expected_login_text in browser.find_element_by_tag_name("body").text

        # go manually to the Product Database Homepage - you must be redirected to the login screen
        browser.get(live_server + reverse("productdb:home"))
        assert expected_homepage_text not in browser.find_element_by_tag_name("body").text
        assert expected_login_text, browser.find_element_by_tag_name("body").text

        # verify, that the "continue without login" button is not visible
        assert expected_login_continue_text not in browser.find_element_by_tag_name("body").text

        # create a product list in the database
        test_pl_name = "Test Product List"
        test_pl_description = "A sample description for the Product List."
        test_pl_product_list_ids = "C2960X-STACK;CAB-ACE\nWS-C2960-24TT-L;WS-C2960-24TC-S"
        test_pl_product_list_id = "C2960X-STACK"

        pl = mixer.blend("productdb.ProductList", name=test_pl_name,
                         description=test_pl_description, string_product_list=test_pl_product_list_ids,
                         update_user=User.objects.get(username="pdb_admin"))

        # the product list must be reachable, even when in login only mode
        browser.get(live_server + reverse("productdb:share-product_list", kwargs={"product_list_id": pl.id}))

        # verify some basic attributes of the page
        body = browser.find_element_by_tag_name("body").text
        assert test_pl_name in body
        assert test_pl_description in body
        assert test_pl_product_list_id in body
        assert "maintained by %s" % self.ADMIN_DISPLAY_NAME in body
        assert "%s</a>" % test_pl_product_list_id not in body, \
            "Link to Product Details should not be available"

        # login as API user
        browser.get(live_server + reverse("productdb:home"))
        browser.find_element_by_id("username").send_keys(self.API_USERNAME)
        browser.find_element_by_id("password").send_keys(self.API_PASSWORD)
        browser.find_element_by_id("login_button").click()

        # the Product Database Homepage must be visible
        assert expected_homepage_text in browser.find_element_by_tag_name("body").text

        # disable the login only mode
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_logout").click()

        browser.find_element_by_id("username").send_keys(self.ADMIN_USERNAME)
        browser.find_element_by_id("password").send_keys(self.ADMIN_PASSWORD)
        browser.find_element_by_id("login_button").click()

        browser.find_element_by_id("navbar_admin").click()
        browser.find_element_by_id("navbar_admin_settings").click()
        assert "Settings" in browser.find_element_by_tag_name("body").text
        browser.find_element_by_id("id_login_only_mode").click()
        browser.find_element_by_id("submit").click()
        assert "Settings saved successfully" in browser.find_element_by_tag_name("body").text

        # end session
        self.logout_user(browser)

    def test_change_password(self, browser, live_server):
        # login as the default API user
        browser.get(live_server + reverse("login"))

        browser.find_element_by_id("username").send_keys("api")
        browser.find_element_by_id("password").send_keys("api")
        browser.find_element_by_id("login_button").click()

        # go to the change password dialog
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_change_password").click()

        assert "Old password" in browser.find_element_by_tag_name("body").text

        # chang the password to api1234
        browser.find_element_by_id("id_old_password").send_keys("api")
        browser.find_element_by_id("id_new_password1").send_keys("api1234")
        browser.find_element_by_id("id_new_password2").send_keys("api1234")
        browser.find_element_by_id("submit").click()

        assert "Password change successful" in browser.find_element_by_tag_name("body").text

        # logout
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_logout").click()
        expected_login_text = "Please enter your credentials below."
        assert expected_login_text in browser.find_element_by_tag_name("body").text

        # login with new password
        browser.find_element_by_id("username").send_keys("api")
        browser.find_element_by_id("password").send_keys("api1234")
        browser.find_element_by_id("login_button").click()

        # the Product Database Homepage must be visible
        expected_text = "This database contains information about network equipment like routers and " \
                        "switches from multiple vendors."
        assert expected_text in browser.find_element_by_tag_name("body").text

        # end session
        self.logout_user(browser)


@pytest.mark.usefixtures("base_data_for_test_case")
@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
@pytest.mark.usefixtures("import_default_text_blocks")
@pytest.mark.usefixtures("set_test_config_file")
@selenium_test
class TestUserProfile(BaseSeleniumTest):
    def test_preferred_vendor_user_profile(self, browser, live_server):
        default_vendor = Vendor.objects.get(id=1).name

        browser.get(live_server + reverse("productdb:home"))

        # verify the vendor selection if the user is not logged in
        browser.find_element_by_id("nav_browse").click()
        browser.find_element_by_id("nav_browse_all_vendor_products").click()
        assert "Browse Products by Vendor" in browser.find_element_by_class_name("page-header").text, \
            "Should view the Browse Product by Vendor page"

        # login
        browser.find_element_by_id("navbar_login").click()
        assert "Please enter your credentials below." in browser.find_element_by_tag_name("body").text, \
            "Should view the login page"

        homepage_message = "Browse Products by Vendor"
        self.login_user(browser, self.API_USERNAME, self.API_PASSWORD, homepage_message)

        # verify the selected default vendor
        pref_vendor_select = browser.find_element_by_id("vendor_selection")
        assert default_vendor in pref_vendor_select.text

        # view the edit settings page
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_user_profile").click()
        assert "Edit User Profile" in browser.find_element_by_tag_name("body").text, \
            "Should view the Edit User Profile page"

        # verify that the vendor with the ID 1 is selected
        pref_vendor_select = browser.find_element_by_id("id_preferred_vendor")
        assert default_vendor in pref_vendor_select.text
        pref_vendor_select = Select(pref_vendor_select)

        # change the vendor selection
        changed_vendor_name = "Juniper Networks"
        pref_vendor_select.select_by_visible_text(changed_vendor_name)
        browser.find_element_by_id("submit").send_keys(Keys.ENTER)

        # redirect to the Browse Products by Vendor
        assert "Browse Products by Vendor" in browser.find_element_by_class_name("page-header").text, \
            "Should view the Browse Product by Vendor page"

        # verify that the new default vendor is selected
        pref_vendor_select = browser.find_element_by_id("vendor_selection")
        assert changed_vendor_name in pref_vendor_select.text

        # end session
        self.logout_user(browser)

    def test_email_change_in_user_profile(self, browser, live_server):
        browser.get(live_server + reverse("productdb:home"))

        # login
        browser.find_element_by_id("navbar_login").click()
        assert "Please enter your credentials below." in browser.find_element_by_tag_name("body").text, \
            "Should view the login page"

        homepage_message = "This database contains information about network equipment like routers and switches " \
                           "from multiple vendors."
        self.login_user(browser, self.API_USERNAME, self.API_PASSWORD, homepage_message)

        # view the edit settings page
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_user_profile").click()
        assert "api@localhost.localhost" in browser.find_element_by_id("id_email").get_attribute('value')

        # change email
        new_email = "a@b.com"
        browser.find_element_by_id("id_email").clear()
        browser.find_element_by_id("id_email").send_keys(new_email)
        browser.find_element_by_id("submit").click()

        # verify redirect to homepage
        assert homepage_message in browser.find_element_by_tag_name("body").text, \
            "Should view the homepage after save"
        assert "User Profile successful updated" in browser.find_element_by_tag_name("body").text, \
            "Should view a message that the user profile was saved"

        # verify new value in email address
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_user_profile").click()
        assert new_email in browser.find_element_by_id("id_email").get_attribute('value'), \
            "Show view the correct email address of the user (%s)" % new_email

        # end session
        self.logout_user(browser)

    def test_search_option_in_user_profile(self, browser, live_server):
        search_term = "WS-C2960X-24T(D|S)"
        browser.get(live_server + reverse("productdb:home"))

        # login
        browser.find_element_by_id("navbar_login").click()
        assert "Please enter your credentials below." in browser.find_element_by_tag_name("body").text, \
            "Should view the login page"

        homepage_message = "This database contains information about network equipment like routers and switches " \
                           "from multiple vendors."
        self.login_user(browser, self.API_USERNAME, self.API_PASSWORD, homepage_message)

        # go to the all products view
        browser.find_element_by_id("nav_browse").click()
        browser.find_element_by_id("nav_browse_all_products").click()

        expected_content = "On this page, you can view all products that are stored in the database."
        assert expected_content in browser.find_element_by_tag_name("body").text, \
            "Should display the view all products page"

        # try to search for the product
        browser.find_element_by_id("column_search_Product ID").send_keys(search_term)

        self.wait_for_text_to_be_displayed_in_body_tag(browser, "No matching records found")

        # enable the regular expression search feature in the user profile
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_user_profile").click()

        assert "Contact eMail:" in browser.find_element_by_tag_name("body").text, \
            "Should show the Edit User Profile view"

        browser.find_element_by_id("id_regex_search").click()
        browser.find_element_by_id("submit").click()

        expected_content = "On this page, you can view all products that are stored in the database."
        assert expected_content in browser.find_element_by_tag_name("body").text, \
            "Should redirect to original page"

        browser.find_element_by_id("column_search_Product ID").send_keys(search_term)
        time.sleep(2)

        assert "WS-C2960X-24TS" in browser.find_element_by_tag_name("body").text, \
            "Should show no results (regular expression is used but by default not enabled)"

        assert "WS-C2960X-24TD" in browser.find_element_by_tag_name("body").text, \
            "Should show no results (regular expression is used but by default not enabled)"

        # end session
        self.logout_user(browser)


@pytest.mark.usefixtures("base_data_for_test_case")
@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
@pytest.mark.usefixtures("import_default_text_blocks")
@pytest.mark.usefixtures("set_test_config_file")
@selenium_test
class TestProductLists(BaseSeleniumTest):
    def test_product_list(self, browser, live_server):
        add_button_xpath = "id('product_list_table_wrapper')/div[1]/div[2]/div/div/a[1]"
        edit_button_xpath = "id('product_list_table_wrapper')/div[1]/div[2]/div/div/a[2]"
        delete_button_xpath = "id('product_list_table_wrapper')/div[1]/div[2]/div/div/a[3]"

        test_pl_name = "Test Product List"
        test_pl_description = "A sample description for the Product List."
        test_pl_product_list_ids = "C2960X-STACK;CAB-ACE\nWS-C2960-24TT-L;WS-C2960-24TC-S"
        test_pl_product_list_id = "C2960X-STACK"

        # open the homepage
        browser.get(live_server + reverse("productdb:home"))

        # go to product list view
        browser.find_element_by_id("nav_browse").click()
        browser.find_element_by_id("nav_browse_all_product_lists").click()

        # verify that the add, edit and delete button is not visible
        body = browser.find_element_by_tag_name("body").text

        assert "Add New" not in body
        assert "Edit Selected" not in body
        assert "Delete Selected" not in body

        # login to the page as admin user
        browser.find_element_by_id("navbar_login").click()
        self.login_user(browser, self.ADMIN_USERNAME, self.ADMIN_PASSWORD, "All Product Lists")

        # verify that the add, edit and delete buttons are visible
        body = browser.find_element_by_tag_name("body").text
        assert "Add New" in body
        assert "Edit Selected" in body
        assert "Delete Selected" in body

        # create a new product list
        browser.find_element_by_xpath(add_button_xpath).click()
        body = browser.find_element_by_tag_name("body").text
        assert "Add Product List" in body

        browser.find_element_by_id("id_name").send_keys(test_pl_name)
        browser.find_element_by_id("id_description").send_keys(test_pl_description)
        browser.find_element_by_id("id_string_product_list").send_keys(test_pl_product_list_ids)

        browser.find_element_by_id("submit").click()
        body = browser.find_element_by_tag_name("body").text
        assert "All Product Lists" in body
        assert test_pl_name in body

        # view the newly created product list
        browser.find_element_by_link_text(test_pl_name).click()
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
        time.sleep(1)
        browser.find_element_by_xpath(edit_button_xpath).click()

        browser.find_element_by_id("id_description").send_keys(" EDITED")
        test_pl_description += " EDITED"

        browser.find_element_by_id("submit").click()

        body = browser.find_element_by_tag_name("body").text
        assert test_pl_description in body

        # delete the new product list
        browser.find_element_by_xpath("id('product_list_table')/tbody/tr[1]/td[2]").click()
        time.sleep(1)
        browser.find_element_by_xpath(delete_button_xpath).click()

        body = browser.find_element_by_tag_name("body").text
        assert "Delete Product List" in body

        browser.find_element_by_name("really_delete").click()
        browser.find_element_by_id("submit").click()

        # verify that the product list is deleted
        body = browser.find_element_by_tag_name("body").text
        assert test_pl_description not in body
        assert "Product List %s successfully deleted." % test_pl_name in body

    def test_product_list_share_link(self, browser, live_server):
        test_pl_name = "Test Product List"
        test_pl_description = "A sample description for the Product List."
        test_pl_product_list_ids = "C2960X-STACK;CAB-ACE\nWS-C2960-24TT-L;WS-C2960-24TC-S"
        test_pl_product_list_id = "C2960X-STACK"

        pl = mixer.blend("productdb.ProductList", name=test_pl_name,
                         description=test_pl_description, string_product_list=test_pl_product_list_ids,
                         update_user=User.objects.get(username="pdb_admin"))

        # try to access the share link
        browser.get(live_server + reverse("productdb:share-product_list", kwargs={"product_list_id": pl.id}))

        # verify some basic attributes of the page
        body = browser.find_element_by_tag_name("body").text
        assert test_pl_name in body
        assert test_pl_description in body
        assert test_pl_product_list_id in body
        assert "maintained by %s" % self.ADMIN_DISPLAY_NAME in body
        with pytest.raises(NoSuchElementException):
            browser.find_element_by_link_text(test_pl_product_list_id)


@pytest.mark.usefixtures("base_data_for_test_case")
@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
@pytest.mark.usefixtures("import_default_text_blocks")
@pytest.mark.usefixtures("set_test_config_file")
@selenium_test
class TestProductDatabaseViews(BaseSeleniumTest):
    def test_product_group_view(self, browser, live_server):
        # navigate to the homepage
        browser.get(live_server + reverse("productdb:home"))

        # go to the "All Product Groups" view
        browser.find_element_by_id("nav_browse").click()
        browser.find_element_by_id("nav_browse_all_product_groups").click()

        # verify page by page title
        assert "All Product Groups" in browser.find_element_by_tag_name("body").text

        # test table content
        expected_table_content = """Vendor\nName"""
        table_rows = [
            'Cisco Systems Catalyst 3850',
            'Cisco Systems Catalyst 2960X',
            'Cisco Systems Catalyst 2960',
            'Juniper Networks EX2200',
        ]

        table = browser.find_element_by_id('product_group_table')
        assert expected_table_content in table.text
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

        # verify page title
        assert "Catalyst 2960X Product Group details" in browser.find_element_by_tag_name("body").text

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

        # verify page by title
        assert "C2960X-STACK Product details" in browser.find_element_by_tag_name("body").text

        # verify that the "Internal Product ID" is not visible (because not set)
        app_config = AppSettings()
        assert app_config.get_internal_product_id_label() not in browser.find_element_by_tag_name("body").text

        # add an internal product ID and verify that it is visible
        test_internal_product_id = "123456789-abcdef"
        p = Product.objects.get(product_id="C2960X-STACK")
        p.internal_product_id = test_internal_product_id
        p.save()

        browser.get(detail_link)
        page_text = browser.find_element_by_tag_name("body").text
        assert app_config.get_internal_product_id_label() in page_text
        assert test_internal_product_id in page_text

    def test_browse_product_list_view(self, browser, live_server):
        expected_content = "This database contains information about network equipment like routers and switches " \
                           "from multiple"

        # a user hits the homepage of the product db
        browser.get(live_server + "/productdb/")

        # check that the user sees a table
        page_text = browser.find_element_by_tag_name('body').text
        assert expected_content in page_text

    def test_add_notification_message(self, browser, live_server):
        # go to the Product Database Homepage
        browser.get(live_server + reverse("productdb:home"))

        browser.find_element_by_id("navbar_login").click()

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

        assert "Add Notification Message" in browser.find_element_by_tag_name("body").text

        # add content
        title = "My message title"
        summary_message = "summary message"
        detailed_message = "detailed message"
        browser.find_element_by_id("id_title").send_keys(title)
        browser.find_element_by_id("id_summary_message").send_keys(summary_message)
        browser.find_element_by_id("id_detailed_message").send_keys(detailed_message)
        browser.find_element_by_id("submit").click()

        # verify that the message is visible on the homepage
        assert title in browser.find_element_by_tag_name("body").text
        assert summary_message in browser.find_element_by_tag_name("body").text

        # end session
        self.logout_user(browser)

    def test_browse_products_view(self, browser, live_server):
        expected_cisco_row = "C2960X-STACK Catalyst 2960-X FlexStack Plus Stacking Module 1195.00 USD"
        expected_juniper_row = "EX-SFP-1GE-LX SFP 1000Base-LX Gigabit Ethernet Optics, 1310nm for " \
                               "10km transmission on SMF 1000.00 USD"
        default_vendor = "Cisco Systems"

        # a user hits the browse product list url
        browser.get(live_server + reverse("productdb:browse_vendor_products"))
        time.sleep(5)

        # check that the user sees a table
        page_text = browser.find_element_by_tag_name('body').text
        assert "Showing 1 to" in page_text

        # the user sees a selection field, where the value "Cisco Systems" is selected
        pl_selection = browser.find_element_by_id("vendor_selection")
        assert default_vendor in pl_selection.text
        pl_selection = Select(pl_selection)

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
        assert "%s Product details" % test_product_id in browser.find_element_by_tag_name("body").text

        # reopen the browse vendor products table
        browser.get(live_server + reverse("productdb:browse_vendor_products"))
        time.sleep(5)

        # the user sees a selection field, where the value "Cisco Systems" is selected
        pl_selection = browser.find_element_by_id("vendor_selection")
        assert default_vendor in pl_selection.text
        pl_selection = Select(pl_selection)

        # the user chooses the list named "Juniper Networks" and press the button "view product list"
        pl_selection.select_by_visible_text("Juniper Networks")
        browser.find_element_by_id("submit").send_keys(Keys.ENTER)

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

    def test_browse_products_view_csv_export(self, browser, live_server, test_download_dir):
        # a user hits the browse product list url
        browser.get(live_server + reverse("productdb:browse_vendor_products"))

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
        with open(file, "r+") as f:
            assert "\ufeffProduct ID;Description;List Price;Lifecycle State\n" == f.readline()

    def test_search_function_on_browse_vendor_products_view(self, browser, live_server):
        # a user hits the browse product list url
        browser.get(live_server + reverse("productdb:browse_vendor_products"))
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
        expected_table_content = "Product ID\nProduct Group\nDescription\n" \
                                 "List Price Lifecycle State Internal Product ID"
        table_rows = [
            "WS-C2960X-24PD-L Catalyst 2960X Catalyst 2960-X 24 GigE PoE 370W, 2 x 10G SFP+, "
            "LAN Base 4595.00 USD 2960x-24pd-l",
            "WS-C2960X-24PS-L Catalyst 2960X Catalyst 2960-X 24 GigE PoE 370W, 4 x 1G SFP, "
            "LAN Base 3195.00 USD 2960x-24ps-l",
        ]

        table = browser.find_element_by_id('product_table')
        assert expected_table_content in table.text
        for r in table_rows:
            print(table.text)
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

    def test_browse_all_products_view(self, browser, live_server):
        expected_cisco_row = "Cisco Systems C2960X-STACK Catalyst 2960-X FlexStack Plus Stacking Module 1195.00 USD"
        expected_juniper_row = "Juniper Networks EX-SFP-1GE-LX SFP 1000Base-LX Gigabit Ethernet Optics, 1310nm for " \
                               "10km transmission on SMF 1000.00 USD"

        # a user hits the browse product list url
        browser.get(live_server + reverse("productdb:all_products"))

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
        assert "%s Product details" % test_product_id in browser.find_element_by_tag_name("body").text

    def test_browse_all_products_view_csv_export(self, browser, live_server, test_download_dir):
        # a user hits the browse product list url
        browser.get(live_server + reverse("productdb:all_products"))

        # the user hits the button CSV
        dt_buttons = browser.find_element_by_class_name("dt-buttons")
        dt_buttons.find_element_by_link_text("CSV").click()

        # the file should download automatically (firefox is configured this way)
        time.sleep(2)

        # verify that the file is a CSV formatted field (with ";" as delimiter)
        file = os.path.join(test_download_dir, "export products.csv")
        with open(file, "r+") as f:
            assert "\ufeffVendor;Product ID;Description;List Price;Lifecycle State\n" == f.readline()

    def test_search_function_on_all_products_view(self, browser, live_server):
        # a user hits the browse product list url
        browser.get(live_server + reverse("productdb:all_products"))

        # he enters a search term in the search box
        search_term = "WS-C2960X-24P"
        search_xpath = '//div[@class="col-sm-4"]/div[@id="product_table_filter"]/label/input[@type="search"]'
        search = browser.find_element_by_xpath(search_xpath)
        search.send_keys(search_term)
        time.sleep(3)

        # the table performs the search function and a defined amount of rows is displayed
        expected_table_content = """Vendor\nProduct ID\nDescription\nList Price Lifecycle State"""
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
