from tests.base.django_test_cases import DestructiveProductDbFunctionalTest
from django.test import override_settings


@override_settings(DEMO_MODE=True)
class SettingsPermissionTest(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml']

    def handle_login_dialog(self, username, password, expected_content):
        # perform user login with the given credentials
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Login", page_text)

        self.browser.find_element_by_id("id_username").send_keys(username)
        self.browser.find_element_by_id("id_password").send_keys(password)
        self.browser.find_element_by_id("submit-id-submit").click()
        self.browser.implicitly_wait(3)

        # check that the user sees the expected title
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn(expected_content, page_text, "login failed")

    def test_regular_user_has_no_access_to_settings_pages(self):
        # a user hits the global settings page
        self.browser.get(self.server_url + "/productdb/settings/")
        self.browser.implicitly_wait(3)

        # perform login using the regular API user
        # the user will be logged in but is again redirected to the login dialog because of missing permissions
        self.handle_login_dialog(self.API_USERNAME, self.API_PASSWORD, "Login\nPlease login to modify the data or")

        # logout user
        self.browser.get(self.server_url + "/api-auth/logout/")

    def test_regular_user_has_no_access_to_cisco_api_settings_pages(self):
        # a user hits the Cisco API Settings page
        self.browser.get(self.server_url + "/productdb/settings/crawler/ciscoapi/")
        self.browser.implicitly_wait(3)

        # perform login using the regular API user
        # the user will be logged in but is again redirected to the login dialog because of missing permissions
        self.handle_login_dialog(self.API_USERNAME, self.API_PASSWORD, "Login\nPlease login to modify the data or")

        # logout user
        self.browser.get(self.server_url + "/api-auth/logout/")

    def test_regular_user_has_no_access_to_task_settings_pages(self):
        # a user hits the Cisco API Settings page
        self.browser.get(self.server_url + "/productdb/settings/testtools/")
        self.browser.implicitly_wait(3)

        # perform login using the regular API user
        # the user will be logged in but is again redirected to the login dialog because of missing permissions
        self.handle_login_dialog(self.API_USERNAME, self.API_PASSWORD, "Login\nPlease login to modify the data or")

        # logout user
        self.browser.get(self.server_url + "/api-auth/logout/")

    def test_regular_user_has_no_access_to_import_products_page(self):
        # a user hits the Cisco API Settings page
        self.browser.get(self.server_url + "/productdb/import/products/")
        self.browser.implicitly_wait(3)

        # perform login using the regular API user
        # the user will be logged in but is again redirected to the login dialog because of missing permissions
        self.handle_login_dialog(self.API_USERNAME, self.API_PASSWORD, "Login\nPlease login to modify the data or")

        # logout user
        self.browser.get(self.server_url + "/api-auth/logout/")
