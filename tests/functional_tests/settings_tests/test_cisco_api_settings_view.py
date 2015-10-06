from tests.base.django_test_cases import DestructiveProductDbFunctionalTest
import json


class CiscoApiSettingsTest(DestructiveProductDbFunctionalTest):
    # with Demo Mode, the application does not require a connection to the Cisco API console (calls are bypassed)
    fixtures = ['default_vendors.yaml', 'demo_mode.yaml']

    def test_enable_cisco_api_settings(self):
        # a user hits the global settings page
        self.browser.get(self.server_url + "/productdb/settings/")
        self.browser.implicitly_wait(3)

        # perform user login with admin user
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Product DB Login", page_text)

        self.browser.find_element_by_id("id_username").send_keys(self.ADMIN_USERNAME)
        self.browser.find_element_by_id("id_password").send_keys(self.ADMIN_PASSWORD)
        self.browser.find_element_by_id("submit-id-submit").click()
        self.browser.implicitly_wait(3)

        # check that the user sees the title
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Product DB Settings", page_text)

        # check that there is the external API settings area and activate
        # the general use of the Cisco API
        self.assertIn("Cisco API settings", page_text)
        self.browser.find_element_by_id("id_cisco_api_enabled").click()
        self.browser.find_element_by_id("submit").click()
        self.browser.implicitly_wait(3)

        # after the refresh of the page, a modify settings button is visible
        page_text = self.browser.find_element_by_tag_name('body').text
        self.browser.implicitly_wait(3)
        self.assertIn("modify settings", page_text)

        self.browser.find_element_by_link_text("modify settings").click()
        self.browser.implicitly_wait(3)

        # now, the user is navigated to the Cisco API console settings
        page_text = self.browser.find_element_by_tag_name("body").text
        self.assertIn("Cisco API Console settings", page_text)

        # because there are no credentials available, the user will see en error message
        initial_error_message = "Verification of the API access failed"
        self.assertIn(initial_error_message, page_text)

        # enter the credentials from the file "ciscoapi.client_credentials.json.bak" and
        # save the settings
        f = open("ciscoapi.client_credentials.json.bak")
        credentials = json.loads(f.read())

        api_client_id = self.browser.find_element_by_id("id_cisco_api_client_id")
        api_client_id.clear()
        api_client_id.send_keys(credentials['client_id'])

        api_client_secret = self.browser.find_element_by_id("id_cisco_api_client_secret")
        api_client_secret.clear()
        api_client_secret.send_keys(credentials['client_secret'])

        self.browser.find_element_by_id("submit").click()
        self.browser.implicitly_wait(5)

        # after the page refreshes, the user will see a message that the connection to the
        # Hello API was successful (test case running in demo mode, anything will work)
        success_message = "The Cisco Hello API is accessible using the credentials below ("
        page_text = self.browser.find_element_by_tag_name("body").text
        self.assertIn(success_message, page_text)

        # enable the synchronization with the Cisco EoX states and click save settings
        self.browser.find_element_by_id("id_eox_api_auto_sync_enabled").click()

        self.browser.find_element_by_id("submit").click()
        self.browser.implicitly_wait(5)

        # after the page refreshes a more detailed configuration section for the synchronization of the Cisco EoX states
        # is visible
        header_text = "This synchronization tasks utilizes the Cisco EoX API and will automatically update the " \
                      "lifecycle state of the products from the given queries."
        page_text = self.browser.find_element_by_tag_name("form").text
        self.assertIn(header_text, page_text)

        # verify that you will see the following elements: auto-create new products, Cisco EoX API queries and the
        # blacklist elements, enter query string and blacklist entries and click submit
        self.assertIn("Settings for periodic synchronization of the Cisco EoX states", page_text)
        auto_create_new_products = self.browser.find_element_by_id("id_eox_auto_sync_auto_create_elements")
        auto_create_new_products.click()

        queries = self.browser.find_element_by_id("id_eox_api_queries")
        queries.send_keys("WS-C\nABC")

        blacklist = self.browser.find_element_by_id("id_eox_api_blacklist")
        blacklist.send_keys("WS-C3750;WS-C2960")

        self.browser.find_element_by_id("submit").click()
        self.browser.implicitly_wait(5)

        # verify the content of the query and blacklist field
        auto_create_new_products = self.browser.find_element_by_id("id_eox_auto_sync_auto_create_elements")
        self.assertTrue(auto_create_new_products.is_selected())

        queries = self.browser.find_element_by_id("id_eox_api_queries")
        self.assertEquals(queries.text, "WS-C\nABC")

        blacklist = self.browser.find_element_by_id("id_eox_api_blacklist")
        self.assertEquals(blacklist.text, "WS-C3750;WS-C2960")

        # go back to the global settings
        self.browser.get(self.server_url + "/productdb/settings/")
        self.browser.implicitly_wait(3)

        # disable the Cisco API console access
        self.browser.find_element_by_id("id_cisco_api_enabled").click()
        self.browser.find_element_by_id("submit").click()
        self.browser.implicitly_wait(3)

        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertNotIn("modify settings", page_text)

        # navigate manually to the cisco api configuration page
        self.browser.get(self.server_url + "/productdb/settings/crawler/ciscoapi/")
        self.browser.implicitly_wait(5)

        # verify that the following error message is displayed
        error_msg = "Please activate the Cisco API access on the global configuration page."

        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn(error_msg, page_text)
