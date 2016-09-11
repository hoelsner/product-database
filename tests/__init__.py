"""
common objects for the selenium test cases
"""
import pytest
import os
import redis
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

PRODUCTS_API_ENDPOINT = "/productdb/api/v0/products/"
PRODUCT_GROUPS_API_ENDPOINT = "/productdb/api/v0/productgroups/"


class BaseSeleniumTest:
    """some utility functions for the selenium test cases"""
    ADMIN_USERNAME = "pdb_admin"
    ADMIN_PASSWORD = "pdb_admin"
    API_USERNAME = "api"
    API_PASSWORD = "api"

    # text blocks for page verification
    HOMEPAGE_TEXT_FOR_VALIDATION = "This database contains information about network equipment like routers " \
                                   "and switches from multiple vendors."

    @staticmethod
    def wait_for_text_to_be_displayed_in_id_tag(browser, component_id, text):
        try:
            WebDriverWait(browser, 10).until(
                EC.text_to_be_present_in_element((By.ID, component_id), text)
            )

        except TimeoutException:
            print(browser.find_element_by_tag_name("body").text)
            pytest.fail("expected text '%s' was not visible within 10 seconds")

    @staticmethod
    def wait_for_text_to_be_displayed_in_body_tag(browser, text):
        try:
            WebDriverWait(browser, 10).until(
                EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text)
            )

        except TimeoutException:
            print(browser.find_element_by_tag_name("body").text)
            pytest.fail("expected text '%s' was not visible within 10 seconds")

    @staticmethod
    def wait_for_element_to_be_clickable_by_xpath(browser, xpath):
        try:
            WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )

        except TimeoutException:
            print(browser.find_element_by_tag_name("body").text)
            pytest.fail("expected text '%s' was not visible within 10 seconds")

    @staticmethod
    def handle_upload_dialog(browser, filename, verify_that_file_exists=True,
                             suppress_notification=False, update_only=False):
        """handle the Excel import dialog"""
        if not os.path.isfile(filename) and verify_that_file_exists:
            pytest.fail("local file for upload not found: %s" % filename)

        if not suppress_notification:
            browser.find_element_by_id("id_suppress_notification").click()

        if update_only:
            browser.find_element_by_id("id_update_existing_products_only").click()

        browser.find_element_by_id("id_excel_file").send_keys(filename)
        browser.find_element_by_id("submit").click()

    @staticmethod
    def is_redis_running():
        try:
            rs = redis.Redis("localhost")
            rs.ping()
            return True

        except:
            return False

    @staticmethod
    def login_user(browser, username, password, expected_content):
        """Handle the login dialog"""
        # perform user login with the given credentials
        page_text = browser.find_element_by_tag_name('body').text
        assert "Login" in page_text, "Should be the login dialog"

        browser.find_element_by_id("username").send_keys(username)
        browser.find_element_by_id("password").send_keys(password)
        browser.find_element_by_id("login_button").click()

        # check that the user sees the expected title
        page_text = browser.find_element_by_tag_name('body').text
        assert expected_content in page_text, "login may failed"

    @staticmethod
    def logout_user(browser):
        """Logout the user"""
        browser.find_element_by_id("navbar_loggedin").click()
        element = browser.find_element_by_id("navbar_loggedin_logout")
        if element:
            # if not found there is no active user session
            element.click()
            page_text = browser.find_element_by_tag_name("body").text
            assert "Please enter your credentials below." in page_text
