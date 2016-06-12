import configparser
import time

from django.core.urlresolvers import reverse
from django.test import override_settings
from selenium.webdriver.common.keys import Keys
from tests.base.django_test_cases import DestructiveProductDbFunctionalTest

"""
This test case requires valid Cisco API client credentials with valid EoX Version 5 API permissions in a configuration
file with the name `product_database.cisco_api_test.config` within the `conf` directory.
"""


class SyncLocalDatabaseWithCiscoApi(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml', ]
    cisco_ios_credentials_config = "conf/product_database.cisco_api_test.config"

    """
    ####################################################################################################################
    # helper methods
    """
    def configure_cisco_api_for_test_case(self):
        # a user hits the global settings page
        self.browser.get(self.server_url + reverse("productdb_config:change_settings"))
        self.browser.implicitly_wait(3)

        # perform user login with admin user
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Login", page_text)

        self.browser.find_element_by_id("username").send_keys(self.ADMIN_USERNAME)
        self.browser.find_element_by_id("password").send_keys(self.ADMIN_PASSWORD)
        self.browser.find_element_by_id("login_button").click()

        # check that the user sees the title
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Settings", page_text)

        # check that there is the External API settings area and activate
        # the general use of the Cisco API
        self.assertIn("External API Settings", page_text)
        self.assertIn("Enable Cisco API", page_text)
        self.browser.find_element_by_id("id_cisco_api_enabled").click()
        self.browser.find_element_by_id("submit").click()

        # after the refresh of the page, a new tab is visible (move to different tasks)
        self.browser.find_element_by_link_text("Cisco API settings").click()
        time.sleep(1)

        # now, the user is navigated to the Cisco API Console settings
        page_text = self.browser.find_element_by_tag_name("body").text
        self.assertIn("Cisco API authentication settings", page_text)

        # enter the credentials from the file "conf/product_database.cisco_api_test.config" and
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
        # Cisco EoX API was successful
        success_message = "Successfully connected to the Cisco EoX API"
        page_text = self.browser.find_element_by_tag_name("body").text
        self.assertIn(success_message, page_text)

        # change to Cisco API configuration tab
        self.browser.find_element_by_link_text("Cisco API settings").click()

        # enable the automatic synchronization with the Cisco EoX states and click save settings
        self.browser.find_element_by_id("id_eox_api_auto_sync_enabled").click()
        self.browser.find_element_by_id("submit").click()

        # change to Cisco API configuration tab
        self.browser.find_element_by_link_text("Cisco API settings").click()
        time.sleep(1)

        # After the page refreshes the more detailed configuration section for the synchronization of the Cisco EoX
        # is visible
        header_text = "If enabled, a new products will be create (if not already existing) i"
        page_text = self.browser.find_element_by_tag_name("form").text
        self.assertIn(header_text, page_text)

        # verify that you will see the following elements: Auto-create new products, Cisco EoX API Queries and the
        # Blacklist elements, enter query string and blacklist entries and click submit
        self.assertIn(header_text, page_text)

        queries = self.browser.find_element_by_id("id_eox_api_queries")
        queries.send_keys("WS-C2960-24-*\nWS-C3750-24-*")

        blacklist = self.browser.find_element_by_id("id_eox_api_blacklist")
        blacklist.send_keys("WS-C2960-24-S-WS;WS-C2960-24-S-RF")

        self.browser.find_element_by_id("submit").click()

        # change to Cisco API configuration tab
        self.browser.find_element_by_link_text("Cisco API settings").click()
        time.sleep(1)

        # Verify the content of the query and blacklist field
        queries = self.browser.find_element_by_id("id_eox_api_queries")
        self.assertEquals(queries.text, "WS-C2960-24-*\nWS-C3750-24-*")

        blacklist = self.browser.find_element_by_id("id_eox_api_blacklist")
        self.assertEquals(blacklist.text, "WS-C2960-24-S-WS;WS-C2960-24-S-RF")

    """
    ####################################################################################################################
    # test cases
    """

    # enable inline processing of celery tasks (no worker required)
    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True)
    def test_configure_periodic_cisco_api_eox_sync_and_trigger_the_execution_manually(self):
        if not self.is_redis_running():
            self.skipTest("local redis server not running, but required for the test case")

        # configure Cisco API access
        self.configure_cisco_api_for_test_case()

        # goto Product Database status page
        self.browser.find_element_by_id("navbar_admin").click()
        self.browser.find_element_by_id("navbar_admin_status").click()
        self.assertIn("Product Database Status", self.browser.find_element_by_tag_name("body").text)

        # verify, that the Cisco API is enabled
        self.assertIn("successful connected to the Cisco EoX API", self.browser.find_element_by_tag_name("body").text)

        # start the synchronization with the Cisco EoX API now
        self.browser.find_element_by_id("trigger_sync_with_cisco_eox_api").click()

        # verify the resulting dialog
        self.assertIn(
            "The following products are affected by this update:",
            self.browser.find_element_by_tag_name("body").text
        )

        # click on continue button, the status page should be visible again
        self.browser.find_element_by_id("continue_button").click()
        self.assertIn("Product Database Status", self.browser.find_element_by_tag_name("body").text)

        # goto the homepage
        self.browser.find_element_by_id("navbar_home").click()

        # on the homepage, you should see a recent message from the Cisco EoX API sync
        self.assertIn(
            "recent events",
            self.browser.find_element_by_tag_name("body").text
        )
        self.assertIn(
            "Synchronization with Cisco EoX API",
            self.browser.find_element_by_tag_name("body").text
        )
        self.assertIn(
            "The synchronization was performed successfully.",
            self.browser.find_element_by_tag_name("body").text
        )

        # show the detailed message
        self.browser.find_element_by_link_text("view details").click()
        self.assertIn(
            "Synchronization with Cisco EoX API",
            self.browser.find_element_by_tag_name("body").text
        )
        self.assertIn(
            "The synchronization was performed successfully. 0 products are updated, "
            "0 products are added to the database and 2 products are ignored",
            self.browser.find_element_by_tag_name("body").text
        )

    def test_configure_periodic_cisco_api_eox_sync_and_perform_initial_synchronization_using_testing_tool(self):
        # configure Cisco API access
        self.configure_cisco_api_for_test_case()

        # switch to the testing tools page and test Cisco EoX API query
        self.browser.get(self.server_url + reverse("cisco_api:eox_query"))

        # enter "WS-C2960-*" as query and check that this query should be executed
        self.browser.find_element_by_id("sync_cisco_eox_states_query").send_keys("WS-C2960-*")
        self.browser.find_element_by_id("sync_cisco_eox_states_now").click()

        # execute query to test API update
        self.browser.find_element_by_id("submit").click()

        # check lifecycle values of WS-C2960-48TT-L using the REST API (should be now not null)
        direct_query_result_log = self.browser.find_element_by_id("direct_query_result_log").text
        updated_element = """"PID": "WS-C2960-48TT-L",
        "blacklist": false,
        "created": false,
        "message": null,
        "updated": true"""
        blacklisted_element = """"PID": "WS-C2960-24-S-RF",
        "blacklist": true,
        "created": false,
        "message": null,
        "updated": false"""
        invalid_element = """"PID": "WS-C2960-24LC-S-WS",
        "blacklist": false,
        "created": false,
        "message": null,
        "updated": false"""

        self.assertIn(updated_element, direct_query_result_log)
        self.assertIn(blacklisted_element, direct_query_result_log)
        self.assertIn(invalid_element, direct_query_result_log)

        # switch to Cisco API settings and activate the auto-create feature
        self.browser.get(self.server_url + reverse("productdb_config:change_settings"))

        # change to Cisco API configuration tab
        self.browser.find_element_by_link_text("Cisco API settings").click()
        time.sleep(1)

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
        self.browser.get(self.server_url + reverse("cisco_api:eox_query"))

        # execute the same query and execute it again
        # enter "WS-C2960-*" as query and check that this query should be executed
        self.browser.find_element_by_id("sync_cisco_eox_states_query").send_keys("WS-C2960-*")
        self.browser.find_element_by_id("sync_cisco_eox_states_now").click()

        # execute query to test API update
        self.browser.find_element_by_id("submit").click()

        # check lifecycle values of WS-C2960-48TT-L using the REST API (should be now not null)
        direct_query_result_log = self.browser.find_element_by_id("direct_query_result_log").text
        created_element = """PID": "WS-C2960-24PC-L",
        "blacklist": false,
        "created": true,
        "message": null,
        "updated": true"""

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
        self.browser.get(self.server_url + reverse("productdb_config:change_settings"))

        # disable the Cisco API console access
        self.browser.find_element_by_id("id_cisco_api_enabled").click()
        self.browser.find_element_by_id("submit").click()

        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertNotIn("Cisco API settings", page_text)
