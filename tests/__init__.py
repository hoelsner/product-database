"""
common objects for the selenium test cases
"""
import json
import pytest
import os
import time
import requests
from requests.auth import HTTPBasicAuth
from urllib import parse
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

PRODUCTS_API_ENDPOINT = "/productdb/api/v1/products/"
PRODUCT_LISTS_API_ENDPOINT = "/productdb/api/v1/productlists/"
NOTIFICATION_MESSAGES_API_ENDPOINT = "/productdb/api/v1/notificationmessages/"
PRODUCT_GROUPS_API_ENDPOINT = "/productdb/api/v1/productgroups/"


class ProductDatabaseAPIHelper:
    """
    Helper class to interact with the Product Database API
    """
    @staticmethod
    def create_product(liveserver_url, product_id, vendor_id,
                       internal_product_id=None,
                       eol_ext_announcement_date=None,
                       end_of_sale_date=None,
                       eox_update_time_stamp=None):
        response = requests.post(liveserver_url + PRODUCTS_API_ENDPOINT,
                                 auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps({
                                     "product_id": product_id,
                                     "vendor": vendor_id,
                                     "internal_product_id": internal_product_id,
                                     "eol_ext_announcement_date": eol_ext_announcement_date,
                                     "end_of_sale_date": end_of_sale_date,
                                     "eox_update_time_stamp": eox_update_time_stamp
                                 }),
                                 verify=False,
                                 timeout=10)

        assert response.ok is True, response.status_code

        return response.json()

    @staticmethod
    def update_product(liveserver_url, product_id, vendor_id=None,
                       internal_product_id=None,
                       eol_ext_announcement_date=None,
                       end_of_sale_date=None,
                       eox_update_time_stamp=None):
        p = ProductDatabaseAPIHelper.get_product_by_product_id(liveserver_url, product_id)

        if vendor_id:
            p["vendor_id"] = vendor_id
        if eol_ext_announcement_date:
            p["eol_ext_announcement_date"] = eol_ext_announcement_date
        if end_of_sale_date:
            p["end_of_sale_date"] = end_of_sale_date
        if eox_update_time_stamp:
            p["eox_update_time_stamp"] = eox_update_time_stamp
        if internal_product_id:
            p["internal_product_id"] = internal_product_id

        response = requests.put(liveserver_url + PRODUCTS_API_ENDPOINT + "%d/" % p["id"],
                                auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                headers={'Content-Type': 'application/json'},
                                data=json.dumps(p),
                                verify=False,
                                timeout=10)

        assert response.ok is True, response.status_code

        return response.json()

    @staticmethod
    def get_product_by_product_id(liveserver_url, product_id):
        response = requests.get(liveserver_url + PRODUCTS_API_ENDPOINT + "?product_id=" + parse.quote_plus(product_id),
                                auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                headers={'Content-Type': 'application/json'},
                                verify=False,
                                timeout=10)

        assert response.ok is True, response.status_code

        response_json = response.json()
        assert len(response_json["data"]) == 1, response_json
        return response.json()["data"][0]

    @staticmethod
    def get_product_list_by_name(liveserver_url, product_list_name):
        response = requests.get(liveserver_url + PRODUCT_LISTS_API_ENDPOINT + "?name=" + parse.quote_plus(
                                    product_list_name
                                ),
                                auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                headers={'Content-Type': 'application/json'},
                                verify=False,
                                timeout=10)

        assert response.ok is True, response.status_code

        response_json = response.json()
        assert len(response_json["data"]) == 1, response_json
        return response.json()["data"][0]

    @staticmethod
    def drop_all_data(liveserver_url):
        response = requests.get(liveserver_url + PRODUCTS_API_ENDPOINT + "?page_size=100",
                                auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                headers={'Content-Type': 'application/json'},
                                verify=False,
                                timeout=10)

        assert response.ok is True
        data = response.json()

        for product in data["data"]:
            r = requests.delete(liveserver_url + PRODUCTS_API_ENDPOINT + "%s/" % product["id"],
                                auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                headers={'Content-Type': 'application/json'},
                                verify=False,
                                timeout=10)

            assert r.ok, "Cannot drop Product ID %s" % product

        response = requests.get(liveserver_url + PRODUCT_GROUPS_API_ENDPOINT + "?page_size=100",
                                auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                headers={'Content-Type': 'application/json'},
                                verify=False,
                                timeout=10)

        assert response.ok is True
        data = response.json()

        for product_group in data["data"]:
            r = requests.delete(liveserver_url + PRODUCT_GROUPS_API_ENDPOINT + "%s/" % product_group["id"],
                                auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                headers={'Content-Type': 'application/json'},
                                verify=False,
                                timeout=10)

            assert r.ok, "Cannot drop Product ID %s" % product

        response = requests.get(liveserver_url + NOTIFICATION_MESSAGES_API_ENDPOINT + "?page_size=100",
                                auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                headers={'Content-Type': 'application/json'},
                                verify=False,
                                timeout=10)

        assert response.ok is True
        data = response.json()

        for notificationmessage in data["data"]:
            r = requests.delete(liveserver_url + NOTIFICATION_MESSAGES_API_ENDPOINT +
                                "%s/" % notificationmessage["id"],
                                auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                headers={'Content-Type': 'application/json'},
                                verify=False,
                                timeout=10)

            assert r.ok, "Cannot drop Notification Message ID %s" % notificationmessage

    @staticmethod
    def load_base_test_data(liveserver_url):
        files = [
            os.path.join("tests", "data", "cisco_test_data.json"),
            os.path.join("tests", "data", "juniper_test_data.json")
        ]
        vendors = {
            "Cisco Systems": 1,
            "Juniper Networks": 2
        }
        productgroup_ids = {}
        for file in files:
            with open(file) as f:
                jdata = json.loads(f.read())

            productgroups = jdata["product_groups"]
            products = jdata["products"]

            for productgroup in productgroups:
                productgroup['vendor'] = vendors[productgroup['vendor']]
                response = requests.post(liveserver_url + PRODUCT_GROUPS_API_ENDPOINT,
                                         auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                         data=json.dumps(productgroup),
                                         headers={'Content-Type': 'application/json'},
                                         verify=False,
                                         timeout=10)
                assert response.ok is True, response.content.decode()
                productgroup_ids[response.json()["name"]] = response.json()["id"]

            for product in products:
                product['vendor'] = vendors[product['vendor']]
                if "product_group" in product:
                    product['product_group'] = productgroup_ids[product['product_group']]
                response = requests.post(liveserver_url + PRODUCTS_API_ENDPOINT,
                                         auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                         data=json.dumps(product),
                                         headers={'Content-Type': 'application/json'},
                                         verify=False,
                                         timeout=10)
                assert response.ok is True, response.content.decode()


class BaseSeleniumTest:
    """some utility functions for the selenium test cases"""
    ADMIN_USERNAME = "pdb_admin"
    ADMIN_PASSWORD = "pdb_admin"
    ADMIN_DISPLAY_NAME = "Admin User"
    API_USERNAME = "api"
    API_PASSWORD = "api"
    API_DISPLAY_NAME = "API User"

    # text blocks for page verification
    HOMEPAGE_TEXT_FOR_VALIDATION = "This database contains information about network equipment like routers " \
                                   "and switches from multiple vendors."

    api_helper = ProductDatabaseAPIHelper()

    @staticmethod
    def wait_for_text_to_be_displayed_in_id_tag(browser, component_id, text):
        try:
            WebDriverWait(browser, 30).until(
                EC.text_to_be_present_in_element((By.ID, component_id), text)
            )

        except TimeoutException:
            print(browser.find_element_by_tag_name("body").text)
            pytest.fail("expected text '%s' was not visible within 10 seconds")

    @staticmethod
    def wait_for_text_to_be_displayed_in_body_tag(browser, text):
        try:
            WebDriverWait(browser, 30).until(
                EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text)
            )

        except TimeoutException:
            print(browser.find_element_by_tag_name("body").text)
            pytest.fail("expected text '%s' was not visible within 10 seconds")

    @staticmethod
    def wait_for_element_to_be_clickable_by_xpath(browser, xpath):
        try:
            WebDriverWait(browser, 30).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )

        except TimeoutException:
            print(browser.find_element_by_tag_name("body").text)
            pytest.fail("expected text '%s' was not visible within 10 seconds")

    @staticmethod
    def handle_upload_dialog(browser, filename, verify_that_file_exists=True,
                             suppress_notification=False, update_only=False):
        """handle the Excel Import Dialogs (Product and Product Migration)"""
        if not os.path.isfile(filename) and verify_that_file_exists:
            pytest.fail("local file for upload not found: %s" % filename)

        if not suppress_notification:
            browser.find_element_by_id("id_suppress_notification").click()

        if update_only:
            browser.find_element_by_id("id_update_existing_products_only").click()

        browser.find_element_by_id("id_excel_file").send_keys(filename)
        browser.find_element_by_id("submit").click()

    @staticmethod
    def login_user(browser, username, password, expected_content):
        """Handle the login dialog"""
        # perform user login with the given credentials
        WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.ID, "username")))
        page_text = browser.find_element_by_tag_name('body').text
        assert "Login" in page_text, "Should be the login dialog"

        browser.find_element_by_id("username").send_keys(username)
        browser.find_element_by_id("password").send_keys(password)
        browser.find_element_by_id("login_button").click()
        WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.ID, "navbar_loggedin")))

        # check that the user sees the expected title
        page_text = browser.find_element_by_tag_name('body').text
        assert expected_content in page_text, "login may failed"

    @staticmethod
    def logout_user(browser):
        """logout the user"""
        time.sleep(3)
        browser.find_element_by_id("navbar_loggedin").click()
        element = browser.find_element_by_id("navbar_loggedin_logout")
        # if not found there is no active user session
        if element:
            element.click()
            WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.ID, "username")))

            page_text = browser.find_element_by_tag_name("body").text
            assert "Please enter your credentials below." in page_text

    @staticmethod
    def take_screenshot(browser):
        browser.get_screenshot_as_file("debug_screenshot.png")
