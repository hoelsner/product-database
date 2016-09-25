"""
Test suite for the selenium test cases
"""
import json
import pytest
import os
import time
from django.core.urlresolvers import reverse
from django.test import Client
from selenium.webdriver.common.keys import Keys
from app.productdb.models import Product, Vendor
from tests import BaseSeleniumTest, PRODUCTS_API_ENDPOINT

pytestmark = pytest.mark.django_db
selenium_test = pytest.mark.skipif(not pytest.config.getoption("--selenium"), reason="need --selenium to run")
online = pytest.mark.skipif(not pytest.config.getoption("--online"), reason="need --online to run")


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
@pytest.mark.usefixtures("import_default_text_blocks")
@pytest.mark.usefixtures("set_test_config_file")
@selenium_test
class TestExcelImportFeature(BaseSeleniumTest):
    @pytest.mark.usefixtures("set_celery_always_eager")
    @pytest.mark.usefixtures("redis_server_required")
    def test_import_product_procedure_with_excel_with_notification(self, browser, live_server):
        # open homepage and login
        browser.get(live_server + reverse("productdb:home"))
        browser.find_element_by_id("navbar_login").click()

        # handle the login dialog
        self.login_user(browser, self.ADMIN_USERNAME, self.ADMIN_PASSWORD, self.HOMEPAGE_TEXT_FOR_VALIDATION)

        # navigate to the import products dialog
        browser.find_element_by_id("navbar_admin").click()
        browser.find_element_by_id("navbar_admin_import_products").click()

        assert "Import Products" in browser.find_element_by_tag_name("body").text

        # add test excel file to dialog and submit the file
        test_excel_file = os.path.join(os.getcwd(), "tests", "data", "excel_import_products_test.xlsx")
        self.handle_upload_dialog(browser, test_excel_file)

        # wait for task to complete
        self.wait_for_text_to_be_displayed_in_id_tag(browser, "status_message", "Products successful updated")

        # verify the output of the upload dialog
        expected_title = "25 Products successful updated"
        expected_contents = [
            "product WS-C2960S-48FPD-L created",
            "product WS-C2960S-48LPD-L created",
            "product WS-C2960S-24PD-L created",
            "product WS-C2960S-48TD-L created",
        ]

        page_text = browser.find_element_by_tag_name("body").text
        assert expected_title in page_text
        for c in expected_contents:
            assert c in page_text

        browser.find_element_by_id("continue_button").click()

        # go to the homepage and verify that the notification message was created (text matching)
        browser.find_element_by_id("navbar_home").click()
        assert "Import product list" in browser.find_element_by_tag_name("body").text

        # verify metric, 25 Products should be imported, 24 with list price (including 0.00 values)
        expected_contents = [
            "All Products\n25",
            "Products with List Price\n24"
        ]

        page_text = browser.find_element_by_tag_name("body").text
        for line in expected_contents:
            assert line in page_text

        # verify the import partially using the API
        parts = [
            {
                "id": "WS-C2960S-48TS-S",
                "expect": [
                    ("product_id", "WS-C2960S-48TS-S"),
                    ("description", "Catalyst 2960S 48 GigE, 2 x SFP LAN Lite"),
                    ("list_price", '3735.00'),
                    ("currency", "USD"),
                    ("vendor", 1),
                ]
            },
            {
                "id": "EX4200-24F-DC",
                "expect": [
                    ("product_id", "EX4200-24F-DC"),
                    ("description", "EX 4200, 24-port  1000BaseX  SFP + 190W DC PS  (optics sold separately), "
                                    "includes 50cm VC cable"),
                    ("list_price", '16300.00'),
                    ("currency", "USD"),
                    ("vendor", 2),
                ]
            }
        ]
        required_keys = ['product_id', 'description', 'list_price', 'currency', 'vendor']
        client = Client()
        client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)
        for part in parts:
            response = client.get(PRODUCTS_API_ENDPOINT + "?product_id=%s" % part['id'])
            assert response.status_code == 200

            response_json = response.json()
            assert response_json["pagination"]["total_records"] == 1

            response_json = response_json["data"][0]
            modified_response = [(k, response_json[k]) for k in required_keys if k in response_json.keys()]
            for s in part['expect']:
                assert s in set(modified_response)

        # end session
        self.logout_user(browser)

    @pytest.mark.usefixtures("set_celery_always_eager")
    @pytest.mark.usefixtures("redis_server_required")
    def test_import_product_procedure_with_excel_without_notification(self, browser, live_server):
        # open homepage and login
        browser.get(live_server + reverse("productdb:home"))
        browser.find_element_by_id("navbar_login").click()

        # handle the login dialog
        self.login_user(browser, self.ADMIN_USERNAME, self.ADMIN_PASSWORD, self.HOMEPAGE_TEXT_FOR_VALIDATION)

        # navigate to the import products dialog
        browser.find_element_by_id("navbar_admin").click()
        browser.find_element_by_id("navbar_admin_import_products").click()

        assert "Import Products" in browser.find_element_by_tag_name("body").text

        # add test excel file to dialog and submit the file
        test_excel_file = os.path.join(os.getcwd(), "tests", "data", "excel_import_products_test.xlsx")
        self.handle_upload_dialog(browser, test_excel_file, suppress_notification=True)

        # wait for task to complete
        self.wait_for_text_to_be_displayed_in_id_tag(browser, "status_message", "Products successful updated")

        # verify the output of the upload dialog
        expected_title = "25 Products successful updated"
        expected_contents = [
            "product WS-C2960S-48FPD-L created",
            "product WS-C2960S-48LPD-L created",
            "product WS-C2960S-24PD-L created",
            "product WS-C2960S-48TD-L created",
        ]

        page_text = browser.find_element_by_tag_name("body").text
        assert expected_title in page_text
        for c in expected_contents:
            assert c in page_text

        browser.find_element_by_id("continue_button").click()

        # go to the homepage and verify that the notification message was created (text matching)
        browser.find_element_by_id("navbar_home").click()
        assert "Import product list" not in browser.find_element_by_tag_name("body").text

        # verify metric, 25 Products should be imported, 24 with list price (including 0.00 values)
        expected_contents = [
            "All Products\n25",
            "Products with List Price\n24"
        ]

        page_text = browser.find_element_by_tag_name("body").text
        for line in expected_contents:
            assert line in page_text

        # end session
        self.logout_user(browser)

    @pytest.mark.usefixtures("set_celery_always_eager")
    @pytest.mark.usefixtures("redis_server_required")
    def test_import_product_procedure_with_excel_in_update_only_mode(self, browser, live_server):
        # create a Product in the database that should be updated
        p = Product.objects.create(product_id="WS-C2960S-48FPD-L", vendor=Vendor.objects.get(id=1))

        # open homepage and login
        browser.get(live_server + reverse("productdb:home"))
        browser.find_element_by_id("navbar_login").click()

        # handle the login dialog
        self.login_user(browser, self.ADMIN_USERNAME, self.ADMIN_PASSWORD, self.HOMEPAGE_TEXT_FOR_VALIDATION)

        # navigate to the import products dialog
        browser.find_element_by_id("navbar_admin").click()
        browser.find_element_by_id("navbar_admin_import_products").click()

        assert "Import Products" in browser.find_element_by_tag_name("body").text

        # add test excel file to dialog and submit the file
        test_excel_file = os.path.join(os.getcwd(), "tests", "data", "excel_import_products_test.xlsx")
        self.handle_upload_dialog(browser, test_excel_file, update_only=True)

        # wait for task to complete
        self.wait_for_text_to_be_displayed_in_id_tag(browser, "status_message", "Products successful updated")

        # verify the output of the upload dialog
        expected_title = "1 Products successful updated"
        expected_content = "product WS-C2960S-48FPD-L updated"

        page_content = browser.find_element_by_tag_name("body").text
        assert expected_title in page_content
        assert expected_content in page_content

        browser.find_element_by_id("continue_button").click()

        # verify the imported entry
        p.refresh_from_db()
        assert p.product_id == "WS-C2960S-48FPD-L"
        assert p.description == "Catalyst 2960S 48 GigE PoE 740W, 2 x 10G SFP+ LAN Base"
        assert p.list_price == 8795.00
        assert p.currency == "USD"
        assert p.vendor.name == "Cisco Systems"

        # end session
        self.logout_user(browser)

    @pytest.mark.usefixtures("set_celery_always_eager")
    def test_import_product_procedure_with_an_excel_file_that_with_incomplete_keys(self, browser, live_server):
        # login and go to the import products page
        browser.get(live_server + reverse("productdb:import_products"))
        self.login_user(browser, self.ADMIN_USERNAME, self.ADMIN_PASSWORD, "Import Products")

        # upload an excel file with invalid keys
        test_excel_file = os.path.join(os.getcwd(),
                                       "tests",
                                       "data",
                                       "excel_import_products_test-invalid_keys.xlsx")
        self.handle_upload_dialog(browser, test_excel_file)

        # verify that the error message appears (in the task status view)
        expected_content = "import failed, invalid file format (not all required keys are found in the Excel file, " \
                           "required keys are: description, list price, product id, vendor)"
        fail_msg_xpath = "//span[@id=\"fail_message\"]"

        self.wait_for_element_to_be_clickable_by_xpath(browser, fail_msg_xpath)
        assert expected_content in browser.find_element_by_xpath(fail_msg_xpath).text
        browser.find_element_by_id("fail_continue").click()

        # end session
        self.logout_user(browser)

    @pytest.mark.usefixtures("set_celery_always_eager")
    def test_import_product_procedure_with_an_excel_file_with_invalid_sheet_name(self, browser, live_server):
        # login and go to the import products page
        browser.get(live_server + reverse("productdb:import_products"))
        self.login_user(browser, self.ADMIN_USERNAME, self.ADMIN_PASSWORD, "Import Products")

        # upload an excel file with invalid keys
        test_excel_file = os.path.join(os.getcwd(),
                                       "tests",
                                       "data",
                                       "excel_import_products_test-invalid_table_name.xlsx")
        self.handle_upload_dialog(browser, test_excel_file)

        # verify that the error message appears (in the task status view)
        expected_content = "import failed, invalid file format (sheet 'products' not found)"
        fail_msg_xpath = "//span[@id=\"fail_message\"]"

        self.wait_for_element_to_be_clickable_by_xpath(browser, fail_msg_xpath)
        assert expected_content in browser.find_element_by_xpath(fail_msg_xpath).text
        browser.find_element_by_id("fail_continue").click()

        # end session
        self.logout_user(browser)


@pytest.mark.usefixtures("base_data_for_test_case")
@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
@pytest.mark.usefixtures("import_default_text_blocks")
@pytest.mark.usefixtures("set_celery_always_eager")
@pytest.mark.usefixtures("set_test_config_file")
@online
@selenium_test
class TestSyncLocalDatabaseWithCiscoEoxApi(BaseSeleniumTest):
    """
    To execute this test suite, you require valid Cisco API client credentials with permissions for the EoX Version 5.
    This credentials must be placed in a JSON formatted file at the root of the project named '.cisco_api_credentials'
    with the following format:

        {
            "client_id": "yourclientid",
            "client_secret": "yourclientsecret"
        }

    """
    def configure_cisco_api_for_test_case(self, browser, live_server):
        browser.get(live_server + reverse("productdb_config:change_settings"))

        # login as admin
        page_text = browser.find_element_by_tag_name('body').text
        assert "Login" in page_text

        browser.find_element_by_id("username").send_keys(self.ADMIN_USERNAME)
        browser.find_element_by_id("password").send_keys(self.ADMIN_PASSWORD)
        browser.find_element_by_id("login_button").click()

        page_text = browser.find_element_by_tag_name('body').text
        assert "Settings" in page_text

        # check that there is the External API settings area and activate the use of the Cisco API
        assert "External API Settings" in page_text
        assert "enable Cisco API" in page_text
        browser.find_element_by_id("id_cisco_api_enabled").click()
        browser.find_element_by_id("submit").click()

        # after the refresh of the page, a new tab is visible (move to different tasks)
        browser.find_element_by_link_text("Cisco API settings").click()
        time.sleep(1)

        # now, the user is navigated to the Cisco API Console settings
        page_text = browser.find_element_by_tag_name("body").text
        assert "Cisco API authentication settings" in page_text

        # enter the credentials from the file ".cisco_api_credentials" and save the settings
        with open(".cisco_api_credentials") as f:
            content = f.read()

        json_credentials = json.loads(content)

        api_client_id = browser.find_element_by_id("id_cisco_api_client_id")
        api_client_id.clear()
        api_client_id.send_keys(json_credentials["client_id"])

        api_client_secret = browser.find_element_by_id("id_cisco_api_client_secret")
        api_client_secret.clear()
        api_client_secret.send_keys(json_credentials["client_secret"])

        browser.find_element_by_id("submit").click()

        # after the page refreshes, the user will see a message that the connection to the Cisco EoX API was successful
        success_message = "Successfully connected to the Cisco EoX API"
        page_text = browser.find_element_by_tag_name("body").text
        assert success_message in page_text

        # change to Cisco API configuration tab
        browser.find_element_by_link_text("Cisco API settings").click()

        # enable the automatic synchronization with the Cisco EoX states and click save settings
        browser.find_element_by_id("id_eox_api_auto_sync_enabled").click()
        browser.find_element_by_id("submit").click()

        # change to Cisco API configuration tab
        browser.find_element_by_link_text("Cisco API settings").click()
        time.sleep(1)

        # After the page refreshes the more detailed configuration section for the synchronization of the Cisco EoX
        # is visible
        header_text = "If enabled, a new products will be create (if not already existing) i"
        page_text = browser.find_element_by_tag_name("form").text
        assert header_text in page_text

        # verify that you will see the following elements: Auto-create new products, Cisco EoX API Queries and the
        # Blacklist elements, enter query string and blacklist entries and click submit
        assert header_text in page_text

        queries = browser.find_element_by_id("id_eox_api_queries")
        queries.send_keys("WS-C2960-24-*\nWS-C3750-24-*")

        blacklist = browser.find_element_by_id("id_eox_api_blacklist")
        blacklist.send_keys("WS-C2960-24-S-WS;WS-C2960-24-S-RF")

        browser.find_element_by_id("submit").click()

        # change to Cisco API configuration tab
        browser.find_element_by_link_text("Cisco API settings").click()
        time.sleep(1)

        # Verify the content of the query and blacklist field
        queries = browser.find_element_by_id("id_eox_api_queries")
        assert queries.text == "WS-C2960-24-*\nWS-C3750-24-*"

        blacklist = browser.find_element_by_id("id_eox_api_blacklist")
        assert blacklist.text == "WS-C2960-24-S-RF\nWS-C2960-24-S-WS"

    @pytest.mark.usefixtures("redis_server_required")
    def test_configure_periodic_cisco_api_eox_sync_and_trigger_the_execution_manually(self, browser, live_server):
        self.configure_cisco_api_for_test_case(browser, live_server)

        # go to the Product Database status page
        browser.find_element_by_id("navbar_admin").click()
        browser.find_element_by_id("navbar_admin_status").click()
        assert "Product Database Status" in browser.find_element_by_tag_name("body").text

        # verify, that the Cisco API is enabled
        assert "successful connected to the Cisco EoX API" in browser.find_element_by_tag_name("body").text

        # start the synchronization with the Cisco EoX API now
        browser.find_element_by_id("trigger_sync_with_cisco_eox_api").click()

        # verify the resulting dialog
        assert "The following products are affected by this update:" in browser.find_element_by_tag_name("body").text

        # click on continue button, the status page should be visible again
        browser.find_element_by_id("continue_button").click()
        assert "Product Database Status" in browser.find_element_by_tag_name("body").text

        # go to the homepage
        browser.find_element_by_id("navbar_home").click()

        # on the homepage, you should see a recent message from the Cisco EoX API sync
        assert "recent events" in browser.find_element_by_tag_name("body").text
        assert "Synchronization with Cisco EoX API" in browser.find_element_by_tag_name("body").text
        assert "The synchronization was performed successfully." in browser.find_element_by_tag_name("body").text

        # show the detailed message
        browser.find_element_by_link_text("view details").click()
        assert "Synchronization with Cisco EoX API" in browser.find_element_by_tag_name("body").text
        expected_content = "The synchronization was performed successfully. 0 products are updated, " \
                           "0 products are added to the database and 2 products are ignored"
        assert expected_content in browser.find_element_by_tag_name("body").text

        # end session
        self.logout_user(browser)

    def test_configure_periodic_cisco_api_eox_sync_and_perform_initial_synchronization_using_testing_tool(self,
                                                                                                          browser,
                                                                                                          live_server):
        self.configure_cisco_api_for_test_case(browser, live_server)

        # switch to the testing tools page and test Cisco EoX API query
        browser.get(live_server + reverse("cisco_api:eox_query"))

        # enter "WS-C2960-*" as query and check that this query should be executed
        browser.find_element_by_id("sync_cisco_eox_states_query").send_keys("WS-C2960-*")
        browser.find_element_by_id("sync_cisco_eox_states_now").click()

        # execute query to test API update
        browser.find_element_by_id("submit").click()

        # check lifecycle values of WS-C2960-48TT-L using the REST API (should be now not null)
        direct_query_result_log = browser.find_element_by_id("direct_query_result_log").text
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

        assert updated_element in direct_query_result_log
        assert blacklisted_element in direct_query_result_log
        assert invalid_element in direct_query_result_log

        # switch to Cisco API settings and activate the auto-create feature
        browser.get(live_server + reverse("productdb_config:change_settings"))

        # change to Cisco API configuration tab
        browser.find_element_by_link_text("Cisco API settings").click()
        time.sleep(1)

        auto_create_new_products = browser.find_element_by_id("id_eox_auto_sync_auto_create_elements")
        auto_create_new_products.click()
        if not auto_create_new_products.is_selected():
            time.sleep(1)
            auto_create_new_products.send_keys(Keys.SPACE)

        browser.find_element_by_id("submit").click()

        # verify results
        auto_create_new_products = browser.find_element_by_id("id_eox_auto_sync_auto_create_elements")
        assert auto_create_new_products.is_selected() is True

        # switch to the testing tools page and test Cisco EoX API query
        browser.get(live_server + reverse("cisco_api:eox_query"))

        # execute the same query and execute it again
        # enter "WS-C2960-*" as query and check that this query should be executed
        browser.find_element_by_id("sync_cisco_eox_states_query").send_keys("WS-C2960-*")
        browser.find_element_by_id("sync_cisco_eox_states_now").click()

        # execute query to test API update
        browser.find_element_by_id("submit").click()

        # check lifecycle values of WS-C2960-48TT-L using the REST API (should be now not null)
        direct_query_result_log = browser.find_element_by_id("direct_query_result_log").text
        created_element = """PID": "WS-C2960-24PC-L",
        "blacklist": false,
        "created": true,
        "message": null,
        "updated": true"""

        assert blacklisted_element in direct_query_result_log
        assert created_element in direct_query_result_log

        # enter an invalid query "AAA BBB" (should not be executed because only a single query is allowed)
        browser.find_element_by_id("sync_cisco_eox_states_query").send_keys("AAA BBB")
        browser.find_element_by_id("sync_cisco_eox_states_now").click()

        # execute query to test API update
        browser.find_element_by_id("submit").click()

        # check result
        direct_query_result_log = browser.find_element_by_id("direct_query_result_log").text
        expected_result = "Invalid query 'AAA BBB': not executed"
        assert expected_result in direct_query_result_log

        # go back to the global settings
        browser.get(live_server + reverse("productdb_config:change_settings"))

        # disable the Cisco API console access
        browser.find_element_by_id("id_cisco_api_enabled").click()
        browser.find_element_by_id("submit").click()

        page_text = browser.find_element_by_tag_name('body').text
        assert "Cisco API settings" not in page_text

        # end session
        self.logout_user(browser)


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
@pytest.mark.usefixtures("import_default_text_blocks")
@pytest.mark.usefixtures("set_test_config_file")
@selenium_test
class TestSettingsPermissions(BaseSeleniumTest):
    def test_regular_user_has_no_access_to_settings_pages(self, browser, live_server):
        browser.get(live_server + reverse("productdb_config:change_settings"))

        # perform login using the regular API user
        # the user will be logged in but is again redirected to the login dialog because of missing permissions
        self.login_user(browser, self.API_USERNAME, self.API_PASSWORD, "HTTP 403 - forbidden request")

        # end session
        browser.get(live_server + reverse("logout"))

    def test_regular_user_has_no_access_to_task_settings_pages(self, browser, live_server):
        browser.get(live_server + reverse("cisco_api:eox_query"))

        # perform login using the regular API user
        # the user will be logged in but is again redirected to the login dialog because of missing permissions
        self.login_user(browser, self.API_USERNAME, self.API_PASSWORD, "HTTP 403 - forbidden request")

        # end session
        browser.get(live_server + reverse("logout"))

    def test_regular_user_has_no_access_to_the_add_notification_settings(self, browser, live_server):
        browser.get(live_server + reverse("productdb_config:notification-add"))

        # perform login using the regular API user
        # the user will be logged in but is again redirected to the login dialog because of missing permissions
        self.login_user(browser, self.API_USERNAME, self.API_PASSWORD, "HTTP 403 - forbidden request")

        # end session
        browser.get(live_server + reverse("logout"))
