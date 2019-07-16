"""
Test suite for the selenium test cases
"""
import datetime
import json
import pytest
import os
import time
import requests
from django.core.urlresolvers import reverse
from django.test import Client
from requests.auth import HTTPBasicAuth
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from tests import BaseSeleniumTest, PRODUCTS_API_ENDPOINT

selenium_test = pytest.mark.skipif(not pytest.config.getoption("--selenium"),
                                   reason="need --selenium to run (implicit usage of the --online flag")
online = pytest.mark.skipif(not pytest.config.getoption("--online"),
                            reason="need --online to run")


@selenium_test
class TestExcelImportFeature(BaseSeleniumTest):
    def test_import_product_procedure_with_excel_with_notification(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)

        # open homepage and login
        browser.get(liveserver + reverse("productdb:home"))
        browser.find_element_by_id("navbar_login").click()

        # handle the login dialog
        self.login_user(browser, self.ADMIN_USERNAME, self.ADMIN_PASSWORD, self.HOMEPAGE_TEXT_FOR_VALIDATION)

        # navigate to the import products dialog
        browser.find_element_by_id("navbar_admin").click()
        browser.find_element_by_id("navbar_admin_import_products").click()
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "id_excel_file")))

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
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "id_excel_file")))

        # go to the homepage and verify that the notification message was created (text matching)
        browser.find_element_by_id("navbar_home").click()
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "search_text_field")))

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
            response = requests.get(liveserver + PRODUCTS_API_ENDPOINT + "?product_id=%s" % part["id"],
                                    auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                    headers={'Content-Type': 'application/json'},
                                    verify=False,
                                    timeout=10)
            assert response.status_code == 200

            response_json = response.json()
            assert response_json["pagination"]["total_records"] == 1

            response_json = response_json["data"][0]
            modified_response = [(k, response_json[k]) for k in required_keys if k in response_json.keys()]
            for s in part['expect']:
                assert s in set(modified_response)

        # end session
        self.logout_user(browser)

    def test_import_product_procedure_with_excel_without_notification(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)

        # open homepage and login
        browser.get(liveserver + reverse("productdb:home"))
        browser.find_element_by_id("navbar_login").click()

        # handle the login dialog
        self.login_user(browser, self.ADMIN_USERNAME, self.ADMIN_PASSWORD, self.HOMEPAGE_TEXT_FOR_VALIDATION)

        # navigate to the import products dialog
        browser.find_element_by_id("navbar_admin").click()
        browser.find_element_by_id("navbar_admin_import_products").click()
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "id_excel_file")))

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

        # go to the homepage and verify that the notification message was created (text matching)
        browser.find_element_by_id("navbar_home").click()
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "search_text_field")))
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

    def test_import_product_procedure_with_excel_in_update_only_mode(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)

        # create a Product in the database that should be updated
        test_product_id = "WS-C2960S-48FPD-L"
        self.api_helper.create_product(liveserver, product_id=test_product_id, vendor_id=1)

        # open homepage and login
        browser.get(liveserver + reverse("productdb:home"))
        browser.find_element_by_id("navbar_login").click()

        # handle the login dialog
        self.login_user(browser, self.ADMIN_USERNAME, self.ADMIN_PASSWORD, self.HOMEPAGE_TEXT_FOR_VALIDATION)

        # navigate to the import products dialog
        browser.find_element_by_id("navbar_admin").click()
        browser.find_element_by_id("navbar_admin_import_products").click()
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "id_excel_file")))

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
        p = self.api_helper.get_product_by_product_id(liveserver, test_product_id)
        assert p["product_id"] == "WS-C2960S-48FPD-L"
        assert p["description"] == "Catalyst 2960S 48 GigE PoE 740W, 2 x 10G SFP+ LAN Base"
        assert p["list_price"] == "8795.00"
        assert p["currency"] == "USD"

        # end session
        self.logout_user(browser)

    def test_import_product_procedure_with_an_excel_file_that_with_incomplete_keys(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)

        # login and go to the import products page
        browser.get(liveserver + reverse("productdb:import_products"))
        self.login_user(browser, self.ADMIN_USERNAME, self.ADMIN_PASSWORD, "Import Products")
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "id_excel_file")))

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

    def test_import_product_procedure_with_an_excel_file_with_invalid_sheet_name(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)

        # login and go to the import products page
        browser.get(liveserver + reverse("productdb:import_products"))
        self.login_user(browser, self.ADMIN_USERNAME, self.ADMIN_PASSWORD, "Import Products")
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "id_excel_file")))

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

    def test_import_product_migrations_procedure(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)

        # create some test data
        self.api_helper.create_product(
            liveserver_url=liveserver,
            product_id="Product A",
            vendor_id=1,
            eol_ext_announcement_date="2016-01-01",
            end_of_sale_date="2016-01-01",
            eox_update_time_stamp=datetime.datetime.utcnow().strftime("%Y-%m-%d"),
        )
        self.api_helper.create_product(
            liveserver_url=liveserver,
            product_id="Product B",
            vendor_id=1,
            eol_ext_announcement_date="2016-01-01",
            end_of_sale_date="2016-01-01",
            eox_update_time_stamp=datetime.datetime.utcnow().strftime("%Y-%m-%d"),
        )
        self.api_helper.create_product(
            liveserver_url=liveserver,
            product_id="Product C",
            vendor_id=1,
            eol_ext_announcement_date="2016-01-01",
            end_of_sale_date="2016-01-01",
            eox_update_time_stamp=datetime.datetime.utcnow().strftime("%Y-%m-%d"),
        )
        self.api_helper.create_product(
            liveserver_url=liveserver,
            product_id="Product D",
            vendor_id=1,
            eol_ext_announcement_date="2016-01-01",
            end_of_sale_date="2016-01-01",
            eox_update_time_stamp=datetime.datetime.utcnow().strftime("%Y-%m-%d"),
        )
        self.api_helper.create_product(
            liveserver_url=liveserver,
            product_id="Product E",
            vendor_id=1,
            eol_ext_announcement_date="2016-01-01",
            end_of_sale_date="2016-01-01",
            eox_update_time_stamp=datetime.datetime.utcnow().strftime("%Y-%m-%d"),
        )

        # login and go to the import products page
        browser.get(liveserver + reverse("productdb:import_product_migrations"))
        self.login_user(browser, self.ADMIN_USERNAME, self.ADMIN_PASSWORD, "Import Product Migrations")

        # upload an excel file with invalid keys
        test_excel_file = os.path.join(os.getcwd(),
                                       "tests",
                                       "data",
                                       "excel_import_product_migrations.xlsx")
        # the button is not pressed in this case
        self.handle_upload_dialog(browser, test_excel_file, suppress_notification=True)

        # wait for task to complete
        self.wait_for_text_to_be_displayed_in_id_tag(browser, "status_message", "Product migrations successful updated")

        # check the message
        expected_message = "create Product Migration path \"Someone\" for Product \"Product A\""
        assert expected_message in browser.find_element_by_tag_name("body").text
        browser.find_element_by_id("continue_button").click()

        # go to Product A and verify that the expected preferred migration option was set
        pa = self.api_helper.get_product_by_product_id(
            liveserver, "Product A"
        )
        browser.get(liveserver + reverse("productdb:product-detail", kwargs={"product_id": pa["id"]}))

        content = browser.find_element_by_tag_name("body").text
        assert "Product ID:\nNot in Database\n" in content
        assert "Source:\nSomeone\n" in content
        assert "Someone (detailed)" in content
        assert "Someone else (detailed)" in content

        # end session
        self.logout_user(browser)


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
    def configure_cisco_api_for_test_case(self, browser, liveserver):
        with open(".cisco_api_credentials") as f:
            json_credentials = json.loads(f.read())

        browser.get(liveserver + reverse("productdb_config:change_settings"))

        # login as admin
        self.login_user(browser=browser, username=self.ADMIN_USERNAME,
                        password=self.ADMIN_PASSWORD, expected_content="Settings")

        page_text = browser.find_element_by_tag_name('body').text
        assert "Settings" in page_text

        # check that there is the External API settings area and activate the use of the Cisco API
        assert "External API Settings" in page_text
        assert "enable Cisco API" in page_text
        browser.find_element_by_id("id_cisco_api_enabled").click()
        browser.find_element_by_id("submit").click()
        time.sleep(5)

        # after the refresh of the page, a new tab is visible (move to different tasks)
        browser.find_element_by_link_text("Cisco API settings").click()
        browser.find_element_by_link_text("Cisco API settings").send_keys(Keys.ENTER)
        time.sleep(5)

        # now, the user is navigated to the Cisco API Console settings
        page_text = browser.find_element_by_tag_name("body").text
        assert "Cisco API authentication settings" in page_text

        # enter the credentials from the file ".cisco_api_credentials" and save the settings
        api_client_id = browser.find_element_by_id("id_cisco_api_client_id")
        api_client_id.clear()
        api_client_id.send_keys(json_credentials["client_id"])

        api_client_secret = browser.find_element_by_id("id_cisco_api_client_secret")
        api_client_secret.clear()
        api_client_secret.send_keys(json_credentials["client_secret"])

        # change to Cisco API configuration tab
        browser.find_element_by_link_text("Cisco API settings").click()

        # enable the automatic synchronization with the Cisco EoX states and click save settings
        browser.find_element_by_id("id_eox_api_auto_sync_enabled").click()
        browser.find_element_by_id("submit").click()
        time.sleep(3)

        # after the submit of the page, select the correct tab
        browser.find_element_by_link_text("Cisco API settings").click()
        browser.find_element_by_link_text("Cisco API settings").send_keys(Keys.ENTER)

        # After the page refreshes the more detailed configuration section for the synchronization of the Cisco EoX
        # is visible
        header_text = "If enabled, new products are created (if not already existing)"
        page_text = browser.find_element_by_tag_name("form").text
        assert header_text in page_text

        # verify that you will see the following elements: Auto-create new products, Cisco EoX API Queries and the
        # Blacklist elements, enter query string and blacklist entries and click submit
        assert header_text in page_text

        browser.find_element_by_id("submit").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Successfully connected to the Cisco EoX API")

        # after the page refreshes, the user will see a message that the connection to the Cisco EoX API was successful
        success_message = "Successfully connected to the Cisco EoX API"
        page_text = browser.find_element_by_tag_name("body").text
        assert success_message in page_text

        # change to Cisco API configuration tab
        browser.find_element_by_link_text("Cisco API settings").click()
        self.wait_for_element_to_be_clickable_by_xpath(browser, "id('id_eox_api_queries')")

        queries = browser.find_element_by_id("id_eox_api_queries")
        queries.send_keys("WS-C2960-24*\nWS-C3750-24*")
        blacklist = browser.find_element_by_id("id_eox_api_blacklist")
        blacklist.send_keys("WS-C2960-24-S-WS;WS-C2960-24-S-RF")

        browser.find_element_by_id("submit").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Successfully connected to the Cisco EoX API")

        # Verify the content of the query and blacklist field
        time.sleep(5)
        browser.find_element_by_link_text("Cisco API settings").click()
        time.sleep(5)
        queries = browser.find_element_by_id("id_eox_api_queries")
        assert queries.text == "WS-C2960-24*\nWS-C3750-24*"

        blacklist = browser.find_element_by_id("id_eox_api_blacklist")
        assert blacklist.text == "WS-C2960-24-S-RF\nWS-C2960-24-S-WS"

    def test_configure_periodic_cisco_api_eox_sync_and_trigger_the_execution_manually(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        self.configure_cisco_api_for_test_case(browser, liveserver)

        # go to the Product Database status page
        browser.find_element_by_id("navbar_admin").click()
        browser.find_element_by_id("navbar_admin_status").click()
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "trigger_sync_with_cisco_eox_api")))

        assert "Product Database Status" in browser.find_element_by_tag_name("body").text

        # verify, that the Cisco API is enabled
        assert "successful connected to the Cisco EoX API" in browser.find_element_by_tag_name("body").text

        # start the synchronization with the Cisco EoX API now
        browser.find_element_by_id("trigger_sync_with_cisco_eox_api").click()

        # verify the resulting dialog
        self.wait_for_text_to_be_displayed_in_id_tag(browser, "status_message", "The following queries were executed")
        page_text = browser.find_element_by_tag_name("body").text
        assert "The following queries were executed:\nWS-C2960-24*" in page_text

        # click on continue button, the status page should be visible again
        browser.find_element_by_id("continue_button").click()
        time.sleep(2)
        assert "Product Database Status" in browser.find_element_by_tag_name("body").text

        # go to the homepage
        browser.find_element_by_id("navbar_home").click()
        time.sleep(2)

        # on the homepage, you should see a recent message from the Cisco EoX API sync
        assert "Recent Notifications" in browser.find_element_by_tag_name("body").text
        assert "Synchronization with Cisco EoX API" in browser.find_element_by_tag_name("body").text
        assert "The synchronization with the Cisco EoX API was" in browser.find_element_by_tag_name("body").text

        # show the detailed message
        browser.find_element_by_link_text("view details").click()
        time.sleep(2)

        assert "The synchronization with the Cisco EoX API was successful." in browser.find_element_by_tag_name("body").text
        expected_content = "The following queries were executed:\n" \
                           "WS-C2960-24* (affects 30 products, success)\n" \
                           "WS-C3750-24* (affects 16 products, success)"
        assert expected_content in browser.find_element_by_tag_name("body").text

        # end session
        self.logout_user(browser)


@selenium_test
class TestSettingsPermissions(BaseSeleniumTest):
    def test_regular_user_has_no_access_to_settings_pages(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)

        browser.get(liveserver + reverse("productdb_config:change_settings"))

        # perform login using the regular API user
        # the user will be logged in but is again redirected to the login dialog because of missing permissions
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "username")))
        page_text = browser.find_element_by_tag_name('body').text
        assert "Login" in page_text, "Should be the login dialog"

        browser.find_element_by_id("username").send_keys(self.API_USERNAME)
        browser.find_element_by_id("password").send_keys(self.API_PASSWORD)
        browser.find_element_by_id("login_button").click()
        time.sleep(3)

        # check that the user sees the expected title
        page_text = browser.find_element_by_tag_name('body').text
        assert "HTTP 403 - forbidden request" in page_text, "login may failed"

        # end session
        browser.get(liveserver + reverse("logout"))

    def test_regular_user_has_no_access_to_the_add_notification_settings(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)

        browser.get(liveserver + reverse("productdb_config:notification-add"))

        # perform login using the regular API user
        # the user will be logged in but is again redirected to the login dialog because of missing permissions
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "username")))
        page_text = browser.find_element_by_tag_name('body').text
        assert "Login" in page_text, "Should be the login dialog"

        browser.find_element_by_id("username").send_keys(self.API_USERNAME)
        browser.find_element_by_id("password").send_keys(self.API_PASSWORD)
        browser.find_element_by_id("login_button").click()
        time.sleep(3)

        # check that the user sees the expected title
        page_text = browser.find_element_by_tag_name('body').text
        assert "HTTP 403 - forbidden request" in page_text, "login may failed"

        # end session
        browser.get(liveserver + reverse("logout"))
