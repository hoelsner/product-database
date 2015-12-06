import time

from selenium.webdriver.common.keys import Keys

from tests.base.django_test_cases import DestructiveProductDbFunctionalTest
import json


"""
This test case requires valid Cisco API client credentials with Hello API and EoX API permissions in a file named
"ciscoapi.client_credentials.json.bak" in the project root.

To work correctly, an internet connection is required.

This test case does not utilize the celery execution engine
"""


class SyncLocalDatabaseWithCiscoApi(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml', ]

    def test_configure_periodic_cisco_api_eox_sync_and_perform_initial_synchronization_using_testing_tool(self):
        # a user hits the global settings page
        self.browser.get(self.server_url + "/productdb/settings/")
        self.browser.implicitly_wait(3)

        # perform user login with admin user
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Login", page_text)

        self.browser.find_element_by_id("id_username").send_keys(self.ADMIN_USERNAME)
        self.browser.find_element_by_id("id_password").send_keys(self.ADMIN_PASSWORD)
        self.browser.find_element_by_id("submit-id-submit").click()

        # check that the user sees the title
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Settings", page_text)

        # check that there is the External API settings area and activate
        # the general use of the Cisco API
        self.assertIn("Cisco API settings", page_text)
        self.browser.find_element_by_id("id_cisco_api_enabled").click()
        self.browser.find_element_by_id("submit").click()

        # After the refresh of the page, a modify settings button is visible
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("modify settings", page_text)

        self.browser.find_element_by_link_text("modify settings").click()

        # now, the user is navigated to the Cisco API Console settings
        page_text = self.browser.find_element_by_tag_name("body").text
        self.assertIn("Cisco API Console settings", page_text)

        # Because there are no credentials available, the user will see en error message
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

        # after the page refreshes, the user will see a message that the connection to the
        # Hello API was successful (test case running in demo mode, anything will work but not triggered)
        success_message = "The Cisco Hello API is accessible using the credentials below (successful connected)."
        page_text = self.browser.find_element_by_tag_name("body").text
        self.assertIn(success_message, page_text)

        # enable the automatic synchronization with the Cisco EoX states and click save settings
        self.browser.find_element_by_id("id_eox_api_auto_sync_enabled").click()

        self.browser.find_element_by_id("submit").click()

        # After the page refreshes a more detailed configuration section for the synchronization of the Cisco EoX states
        # is visible
        header_text = "This synchronization tasks utilizes the Cisco EoX API and will automatically update the " \
                      "lifecycle state of the products from the given queries."
        page_text = self.browser.find_element_by_tag_name("form").text
        self.assertIn(header_text, page_text)

        # verify that you will see the following elements: Auto-create new products, Cisco EoX API Queries and the
        # Blacklist elements, enter query string and blacklist entries and click submit
        self.assertIn("Settings for periodic synchronization of the Cisco EoX states", page_text)

        queries = self.browser.find_element_by_id("id_eox_api_queries")
        queries.send_keys("WS-C2960-24-*\nWS-C3750-24-*")

        blacklist = self.browser.find_element_by_id("id_eox_api_blacklist")
        blacklist.send_keys("WS-C2960-24-S-WS;WS-C2960-24-S-RF")

        self.browser.find_element_by_id("submit").click()

        # Verify the content of the query and blacklist field
        queries = self.browser.find_element_by_id("id_eox_api_queries")
        self.assertEquals(queries.text, "WS-C2960-24-*\nWS-C3750-24-*")

        blacklist = self.browser.find_element_by_id("id_eox_api_blacklist")
        self.assertEquals(blacklist.text, "WS-C2960-24-S-WS;WS-C2960-24-S-RF")

        # switch to the testing tools page and test Cisco EoX API query
        self.browser.get(self.server_url + "/productdb/settings/testtools/")

        # enter "WS-C2960-*" as query and check that this query should be executed
        self.browser.find_element_by_id("sync_cisco_eox_states_query").send_keys("WS-C2960-*")
        self.browser.find_element_by_id("sync_cisco_eox_states_now").click()

        # execute query to test API update
        self.browser.find_element_by_id("submit").click()

        # check lifecycle values of WS-C2960-48TT-L using the REST API (should be now not null)
        direct_query_result_log = self.browser.find_element_by_id("direct_query_result_log").text
        updated_element = "WS-C2960-48TT-L     : data updated"
        blacklisted_element = "WS-C2960-24-S-RF    : blacklisted entry (not updated)"
        invalid_element = "WS-C2960-24LC-S-WS  : product not found in local database"

        self.assertIn(updated_element, direct_query_result_log)
        self.assertIn(blacklisted_element, direct_query_result_log)
        self.assertIn(invalid_element, direct_query_result_log)

        # switch to Cisco API settings and activate the auto-create feature
        self.browser.get(self.server_url + "/productdb/settings/crawler/ciscoapi/")

        auto_create_new_products = self.browser.find_element_by_id("id_eox_auto_sync_auto_create_elements")
        auto_create_new_products.click()
        if not auto_create_new_products.is_selected():
            time.sleep(1)
            auto_create_new_products.send_keys(Keys.SPACE)

        self.browser.find_element_by_id("submit").click()

        # verify results
        auto_create_new_products = self.browser.find_element_by_id("id_eox_auto_sync_auto_create_elements")
        self.assertTrue(auto_create_new_products.is_selected())

        # switch to the testing tools page and test Cisco EoX API query
        self.browser.get(self.server_url + "/productdb/settings/testtools/")

        # execute the same query and execute it again
        # enter "WS-C2960-*" as query and check that this query should be executed
        self.browser.find_element_by_id("sync_cisco_eox_states_query").send_keys("WS-C2960-*")
        self.browser.find_element_by_id("sync_cisco_eox_states_now").click()

        # execute query to test API update
        self.browser.find_element_by_id("submit").click()

        # check lifecycle values of WS-C2960-48TT-L using the REST API (should be now not null)
        direct_query_result_log = self.browser.find_element_by_id("direct_query_result_log").text
        created_element = "WS-C2960-24PC-L     : data updated (created: True)"

        self.assertIn(blacklisted_element, direct_query_result_log)
        self.assertIn(created_element, direct_query_result_log)

        # enter an invalid query "AAA BBB" (should not be executed because only a single query is allowed)
        self.browser.find_element_by_id("sync_cisco_eox_states_query").send_keys("AAA BBB")
        self.browser.find_element_by_id("sync_cisco_eox_states_now").click()

        # execute query to test API update
        self.browser.find_element_by_id("submit").click()

        # check result
        direct_query_result_log = self.browser.find_element_by_id("direct_query_result_log").text
        expected_result = "Invalid query 'AAA BBB': not executed"
        self.assertIn(expected_result, direct_query_result_log)

        # go back to the global settings
        self.browser.get(self.server_url + "/productdb/settings/")

        # disable the Cisco API console access
        self.browser.find_element_by_id("id_cisco_api_enabled").click()
        self.browser.find_element_by_id("submit").click()

        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertNotIn("modify settings", page_text)

        # navigate manually to the cisco api configuration page
        self.browser.get(self.server_url + "/productdb/settings/crawler/ciscoapi/")

        # verify that the following error message is displayed
        error_msg = "Please activate the Cisco API access on the global configuration page."

        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn(error_msg, page_text)
