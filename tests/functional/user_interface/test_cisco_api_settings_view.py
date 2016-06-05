import configparser

from django.core.urlresolvers import reverse
from selenium.webdriver.common.keys import Keys
from django.test import override_settings
from tests.base.django_test_cases import DestructiveProductDbFunctionalTest
import time


@override_settings(DEMO_MODE=True)
class CiscoApiSettingsTest(DestructiveProductDbFunctionalTest):
    # with Demo Mode, the application does not require a connection to the Cisco API console (calls are bypassed)
    fixtures = ['default_vendors.yaml']
    cisco_ios_credentials_config = "conf/product_database.cisco_api_test.config"

    def test_enable_cisco_api_settings(self):
        # a user hits the global settings page
        self.browser.get(self.server_url + reverse("productdb_config:change_settings"))
        self.browser.implicitly_wait(3)

        # perform user login with admin user
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Product Database\nPlease enter your credentials below", page_text)

        self.browser.find_element_by_id("username").send_keys(self.ADMIN_USERNAME)
        self.browser.find_element_by_id("password").send_keys(self.ADMIN_PASSWORD)
        self.browser.find_element_by_id("login_button").click()

        # check that the user sees the title
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Product Database Settings", page_text)

        # check that there is the external API settings area and activate the general use of the Cisco API
        self.assertIn("External API Settings", self.browser.find_element_by_tag_name("body").text)
        self.browser.find_element_by_id("id_cisco_api_enabled").click()
        self.browser.find_element_by_id("submit").click()

        # after the refresh of the page, a new tab is visible
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Cisco API settings", page_text)
        self.browser.find_element_by_link_text("Cisco API settings").click()
        time.sleep(1)

        # now, the user is navigated to the Cisco API console settings
        page_text = self.browser.find_element_by_tag_name("body").text
        self.assertIn("Cisco API authentication settings", page_text)

        # enter the credentials from the file "ciscoapi.client_credentials.json.bak" and
        # save the settings
        config = configparser.ConfigParser()
        config.read(self.cisco_ios_credentials_config)
        credentials = {
            "client_id": config.get(section="cisco_api", option="client_id"),
            "client_secret": config.get(section="cisco_api", option="client_secret")
        }

        api_client_id = self.browser.find_element_by_id("id_cisco_api_client_id")
        api_client_id.clear()
        api_client_id.send_keys(credentials['client_id'])

        api_client_secret = self.browser.find_element_by_id("id_cisco_api_client_secret")
        api_client_secret.clear()
        api_client_secret.send_keys(credentials['client_secret'])

        self.browser.find_element_by_id("submit").click()

        # after the page refreshes, the user will see a message that the connection to the
        # Hello API was successful (test case running in demo mode, anything will work)
        success_message = "Successfully connected to the Cisco EoX API (Demo Mode)"
        page_text = self.browser.find_element_by_tag_name("body").text
        self.assertIn(success_message, page_text)

        # go to the Cisco API settings tab
        self.browser.find_element_by_link_text("Cisco API settings").click()
        time.sleep(1)

        # enable the synchronization with the Cisco EoX states and click save settings
        self.browser.find_element_by_id("id_eox_api_auto_sync_enabled").click()

        self.browser.find_element_by_id("submit").click()
        self.browser.implicitly_wait(5)

        # go to the Cisco API settings tab
        self.browser.find_element_by_link_text("Cisco API settings").click()
        time.sleep(1)

        # after the page refreshes a more detailled Cisco API settings tab is visible
        header_text = "If enabled, a new products will be create (if not already existing) if an EoL message "
        page_text = self.browser.find_element_by_tag_name("form").text
        self.assertIn(header_text, page_text)

        # verify that you will see the following elements: auto-create new products, Cisco EoX API queries and the
        # blacklist elements, enter query string and blacklist entries and click submit
        self.assertIn("Periodic synchronization of the Cisco EoX states:", page_text)
        auto_create_new_products = self.browser.find_element_by_id("id_eox_auto_sync_auto_create_elements")
        auto_create_new_products.send_keys(Keys.SPACE)
        if not auto_create_new_products.is_selected():
            time.sleep(1)
            auto_create_new_products.send_keys(Keys.SPACE)

        queries = self.browser.find_element_by_id("id_eox_api_queries")
        queries.send_keys("WS-C\nABC")

        blacklist = self.browser.find_element_by_id("id_eox_api_blacklist")
        blacklist.send_keys("WS-C3750;WS-C2960")

        self.browser.find_element_by_id("submit").click()
        time.sleep(3)

        # go to the Cisco API settings tab
        self.browser.find_element_by_link_text("Cisco API settings").click()
        time.sleep(1)

        # verify the content of the query and blacklist field
        auto_create_new_products = self.browser.find_element_by_id("id_eox_auto_sync_auto_create_elements")
        self.assertTrue(auto_create_new_products.is_selected())

        queries = self.browser.find_element_by_id("id_eox_api_queries")
        self.assertEquals(queries.text, "WS-C\nABC")

        blacklist = self.browser.find_element_by_id("id_eox_api_blacklist")
        self.assertEquals(blacklist.text, "WS-C3750;WS-C2960")

        # go back to the global settings
        self.browser.get(self.server_url + reverse("productdb_config:change_settings"))

        # disable the Cisco API console access
        self.browser.find_element_by_id("id_cisco_api_enabled").click()
        self.browser.find_element_by_id("submit").click()

        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertNotIn("Cisco API settings", page_text)

        # navigate manually to the cisco api configuration page
        self.browser.get(self.server_url + reverse("cisco_api:eox_query"))

        # verify that the following error message is displayed
        error_msg = "Cisco API disabled:\nPlease activate the Cisco API access within the global configuration page."

        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn(error_msg, page_text)
