from tests.base.django_test_cases import DestructiveProductDbFunctionalTest


class SettingsPermissionTest(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml', 'demo_mode.yaml']

    def test_regular_user_has_no_access_to_settings_pages(self):
        # a user hits the global settings page
        self.browser.get(self.server_url + "/productdb/settings/")
        self.browser.implicitly_wait(3)

        # perform user login with the predefined api user
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Login", page_text)

        self.browser.find_element_by_id("id_username").send_keys(self.API_USERNAME)
        self.browser.find_element_by_id("id_password").send_keys(self.API_PASSWORD)
        self.browser.find_element_by_id("submit-id-submit").click()
        self.browser.implicitly_wait(3)

        # the user is again redirected to the login page
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Login", page_text)

        # logout user
        self.browser.get(self.server_url + "/api-auth/logout/")

    def test_regular_user_has_no_access_to_cisco_api_settings_pages(self):
        # a user hits the Cisco API Settings page
        self.browser.get(self.server_url + "/productdb/settings/crawler/ciscoapi/")
        self.browser.implicitly_wait(3)

        # perform user login with the api user
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Login", page_text)

        self.browser.find_element_by_id("id_username").send_keys(self.API_USERNAME)
        self.browser.find_element_by_id("id_password").send_keys(self.API_PASSWORD)
        self.browser.find_element_by_id("submit-id-submit").click()
        self.browser.implicitly_wait(3)

        # the user is again redirected to the login page
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Login", page_text)

        # logout user
        self.browser.get(self.server_url + "/api-auth/logout/")

    def test_regular_user_has_no_access_to_task_settings_pages(self):
        # a user hits the Cisco API Settings page
        self.browser.get(self.server_url + "/productdb/settings/testtools/")
        self.browser.implicitly_wait(3)

        # perform user login with the api user
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Login", page_text)

        self.browser.find_element_by_id("id_username").send_keys(self.API_USERNAME)
        self.browser.find_element_by_id("id_password").send_keys(self.API_PASSWORD)
        self.browser.find_element_by_id("submit-id-submit").click()
        self.browser.implicitly_wait(3)

        # the user is again redirected to the login page
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Login", page_text)

        # logout user
        self.browser.get(self.server_url + "/api-auth/logout/")
