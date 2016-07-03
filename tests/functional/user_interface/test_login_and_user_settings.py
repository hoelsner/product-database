from django.core.urlresolvers import reverse

from tests.base.django_test_cases import DestructiveProductDbFunctionalTest
from django.test import override_settings


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
