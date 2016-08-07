from django.core.urlresolvers import reverse
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select

from app.productdb.models import Vendor
from tests.base.django_test_cases import DestructiveProductDbFunctionalTest
from django.test import override_settings

import time


@override_settings(DEMO_MODE=True)
class UserActionTests(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml', 'default_text_blocks.yaml']

    def test_change_password(self):
        """
        test the change password function
        """
        # login as superuser
        self.browser.get(self.server_url + reverse("login"))

        self.browser.find_element_by_id("username").send_keys("api")
        self.browser.find_element_by_id("password").send_keys("api")
        self.browser.find_element_by_id("login_button").click()

        # go to the change password dialog
        self.browser.find_element_by_id("navbar_loggedin").click()
        self.browser.find_element_by_id("navbar_loggedin_change_password").click()

        self.assertIn("Old password", self.browser.find_element_by_tag_name("body").text)

        # chang the password to api1234
        self.browser.find_element_by_id("id_old_password").send_keys("api")
        self.browser.find_element_by_id("id_new_password1").send_keys("api1234")
        self.browser.find_element_by_id("id_new_password2").send_keys("api1234")
        self.browser.find_element_by_id("submit").click()

        self.assertIn("Password change successful", self.browser.find_element_by_tag_name("body").text)

        # logout
        self.browser.find_element_by_id("navbar_loggedin").click()
        self.browser.find_element_by_id("navbar_loggedin_logout").click()
        expected_login_text = "Please enter your credentials below."
        self.assertIn(expected_login_text, self.browser.find_element_by_tag_name("body").text)

        # login with new password
        self.browser.find_element_by_id("username").send_keys("api")
        self.browser.find_element_by_id("password").send_keys("api1234")
        self.browser.find_element_by_id("login_button").click()

        # the Product Database Homepage must be visible
        expected_text = "This database contains information about network equipment like routers and " \
                        "switches from multiple vendors."
        self.assertIn(expected_text, self.browser.find_element_by_tag_name("body").text)


@override_settings(DEMO_MODE=True)
class LoginOnlyModeTest(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml', 'default_text_blocks.yaml']

    def test_login_only_mode(self):
        """
        test the login only mode setting of the Product database
        """
        # go to the Product Database Homepage - it must be visible
        self.browser.get(self.server_url + reverse("productdb:home"))
        self.browser.implicitly_wait(3)

        expected_homepage_text = "This database contains information about network equipment like routers and " \
                                 "switches from multiple vendors."
        self.assertIn(expected_homepage_text, self.browser.find_element_by_tag_name("body").text)

        # Login as superuser - verify, that the "continue without login" button is visible
        self.browser.find_element_by_id("navbar_login").click()

        expected_login_continue_text = "continue without login"
        self.assertIn(expected_login_continue_text, self.browser.find_element_by_tag_name("body").text)

        # login as superuser
        self.browser.find_element_by_id("username").send_keys(self.ADMIN_USERNAME)
        self.browser.find_element_by_id("password").send_keys(self.ADMIN_PASSWORD)
        self.browser.find_element_by_id("login_button").click()

        # change settings to login only mode and save settings
        self.browser.find_element_by_id("navbar_admin").click()
        self.browser.find_element_by_id("navbar_admin_settings").click()
        self.assertIn("Settings", self.browser.find_element_by_tag_name("body").text)
        self.browser.find_element_by_id("id_login_only_mode").click()
        self.browser.find_element_by_id("submit").click()
        self.assertIn("Settings saved successfully", self.browser.find_element_by_tag_name("body").text)

        # go to the Product Database Homepage - it must be visible
        self.browser.get(self.server_url + reverse("productdb:home"))
        self.assertIn(expected_homepage_text, self.browser.find_element_by_tag_name("body").text)

        # logout - the login screen is visible
        self.browser.find_element_by_id("navbar_loggedin").click()
        self.browser.find_element_by_id("navbar_loggedin_logout").click()
        expected_login_text = "Please enter your credentials below."
        self.assertIn(expected_login_text, self.browser.find_element_by_tag_name("body").text)

        # go manually to the Product Database Homepage - you must be redirected to the login screen
        self.browser.get(self.server_url + reverse("productdb:home"))
        self.assertNotIn(expected_homepage_text, self.browser.find_element_by_tag_name("body").text)
        self.assertIn(expected_login_text, self.browser.find_element_by_tag_name("body").text)

        # verify, that the "continue without login" button is not visible
        self.assertNotIn(expected_login_continue_text, self.browser.find_element_by_tag_name("body").text)

        # login as API user
        self.browser.find_element_by_id("username").send_keys(self.API_USERNAME)
        self.browser.find_element_by_id("password").send_keys(self.API_PASSWORD)
        self.browser.find_element_by_id("login_button").click()

        # the Product Database Homepage must be visible
        self.assertIn(expected_homepage_text, self.browser.find_element_by_tag_name("body").text)

        # disable the login only mode
        self.browser.find_element_by_id("navbar_loggedin").click()
        self.browser.find_element_by_id("navbar_loggedin_logout").click()

        self.browser.find_element_by_id("username").send_keys(self.ADMIN_USERNAME)
        self.browser.find_element_by_id("password").send_keys(self.ADMIN_PASSWORD)
        self.browser.find_element_by_id("login_button").click()

        self.browser.find_element_by_id("navbar_admin").click()
        self.browser.find_element_by_id("navbar_admin_settings").click()
        self.assertIn("Settings", self.browser.find_element_by_tag_name("body").text)
        self.browser.find_element_by_id("id_login_only_mode").click()
        self.browser.find_element_by_id("submit").click()
        self.assertIn("Settings saved successfully", self.browser.find_element_by_tag_name("body").text)


@override_settings(DEMO_MODE=True)
class UserProfileTest(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml', 'default_text_blocks.yaml']

    def test_preferred_vendor_user_profile(self):
        default_vendor = Vendor.objects.get(id=1).name

        self.browser.get(self.server_url + reverse("productdb:home"))
        self.browser.implicitly_wait(3)

        # verify the vendor selection if the user is not logged in
        self.browser.find_element_by_id("nav_browse").click()
        self.browser.find_element_by_id("nav_browse_all_vendor_products").click()
        self.assertIn(
            "Browse Products by Vendor",
            self.browser.find_element_by_class_name("page-header").text,
            "should view the Browse Product by Vendor page"
        )

        # login
        self.browser.find_element_by_id("navbar_login").click()
        self.assertIn(
            "Please enter your credentials below.",
            self.browser.find_element_by_tag_name("body").text,
            "should view the login page"
        )

        homepage_message = "Browse Products by Vendor"
        self.handle_login_dialog(
            self.API_USERNAME,
            self.API_PASSWORD,
            homepage_message
        )

        # verify the selected default vendor
        pref_vendor_select = self.browser.find_element_by_id("vendor_selection")
        self.assertIn(default_vendor, pref_vendor_select.text)

        # view the edit settings page
        self.browser.find_element_by_id("navbar_loggedin").click()
        self.browser.find_element_by_id("navbar_loggedin_user_profile").click()
        self.assertIn(
            "Edit User Profile",
            self.browser.find_element_by_tag_name("body").text,
            "should view the Edit User Profile page"
        )

        # verify that the vendor with the ID 1 is selected
        pref_vendor_select = self.browser.find_element_by_id("id_preferred_vendor")
        self.assertIn(default_vendor, pref_vendor_select.text)
        pref_vendor_select = Select(pref_vendor_select)

        # change the vendor selection
        changed_vendor_name = "Juniper Networks"
        pref_vendor_select.select_by_visible_text(changed_vendor_name)
        self.browser.find_element_by_id("submit").send_keys(Keys.ENTER)

        # redirect to the Browse Products by Vendor
        self.assertIn(
            "Browse Products by Vendor",
            self.browser.find_element_by_class_name("page-header").text,
            "should view the Browse Product by Vendor page"
        )

        # verify that the new default vendor is selected
        pref_vendor_select = self.browser.find_element_by_id("vendor_selection")
        self.assertIn(changed_vendor_name, pref_vendor_select.text)

    def test_email_change_in_user_profile(self):
        self.browser.get(self.server_url + reverse("productdb:home"))
        self.browser.implicitly_wait(3)

        # login
        self.browser.find_element_by_id("navbar_login").click()
        self.assertIn(
            "Please enter your credentials below.",
            self.browser.find_element_by_tag_name("body").text,
            "should view the login page"
        )

        homepage_message = "This database contains information about network equipment like routers and switches " \
                           "from multiple vendors."
        self.handle_login_dialog(
            self.API_USERNAME,
            self.API_PASSWORD,
            homepage_message
        )

        # view the edit settings page
        self.browser.find_element_by_id("navbar_loggedin").click()
        self.browser.find_element_by_id("navbar_loggedin_user_profile").click()
        self.assertIn(
            "api@localhost.localhost",
            self.browser.find_element_by_id("id_email").get_attribute('value')
        )

        # change email
        new_email = "a@b.com"
        self.browser.find_element_by_id("id_email").clear()
        self.browser.find_element_by_id("id_email").send_keys(new_email)
        self.browser.find_element_by_id("submit").click()

        # verify redirect to homepage
        self.assertIn(
            homepage_message,
            self.browser.find_element_by_tag_name("body").text,
            "should view the homepage after save"
        )
        self.assertIn(
            "User Profile successful updated",
            self.browser.find_element_by_tag_name("body").text,
            "should view a message that the user profile was saved"
        )

        # verify new value in email address
        self.browser.find_element_by_id("navbar_loggedin").click()
        self.browser.find_element_by_id("navbar_loggedin_user_profile").click()
        self.assertIn(
            new_email,
            self.browser.find_element_by_id("id_email").get_attribute('value'),
            "show view the correct email address of the user (%s)" % new_email
        )

    def test_search_option_in_user_profile(self):
        search_term = "WS-C2960X-24T(D|S)"
        self.browser.get(self.server_url + reverse("productdb:home"))
        self.browser.implicitly_wait(3)

        # login
        self.browser.find_element_by_id("navbar_login").click()
        self.assertIn(
            "Please enter your credentials below.",
            self.browser.find_element_by_tag_name("body").text,
            "should view the login page"
        )

        homepage_message = "This database contains information about network equipment like routers and switches " \
                           "from multiple vendors."
        self.handle_login_dialog(
            self.API_USERNAME,
            self.API_PASSWORD,
            homepage_message
        )

        # go to the all products view
        self.browser.find_element_by_id("nav_browse").click()
        self.browser.find_element_by_id("nav_browse_all_products").click()

        self.assertIn(
            "On this page, you can view all products that are stored in the database.",
            self.browser.find_element_by_tag_name("body").text,
            "should display the view all products page"
        )

        # try to search for the product
        self.browser.find_element_by_id("column_search_Product ID").send_keys(search_term)
        time.sleep(4)

        self.assertIn(
            "No matching records found",
            self.browser.find_element_by_tag_name("body").text,
            "should show no results (regular expression is used but by default not enabled)"
        )

        # enable the regular expression search feature in the user profile
        self.browser.find_element_by_id("navbar_loggedin").click()
        self.browser.find_element_by_id("navbar_loggedin_user_profile").click()

        self.assertIn(
            "Contact eMail:",
            self.browser.find_element_by_tag_name("body").text,
            "Should show the Edit User Profile view"
        )

        self.browser.find_element_by_id("id_regex_search").click()
        self.browser.find_element_by_id("submit").click()

        self.assertIn(
            "On this page, you can view all products that are stored in the database.",
            self.browser.find_element_by_tag_name("body").text,
            "should redirect to original page"
        )

        self.browser.find_element_by_id("column_search_Product ID").send_keys(search_term)
        time.sleep(4)

        self.assertIn(
            "WS-C2960X-24TS",
            self.browser.find_element_by_tag_name("body").text,
            "should show no results (regular expression is used but by default not enabled)"
        )
        self.assertIn(
            "WS-C2960X-24TD",
            self.browser.find_element_by_tag_name("body").text,
            "should show no results (regular expression is used but by default not enabled)"
        )
