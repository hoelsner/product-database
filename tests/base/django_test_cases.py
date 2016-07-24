from selenium import webdriver
from django.test import override_settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from tests.api import create_real_test_data
from tests.api import drop_all_products
from tests.base.rest_calls import PRODUCTS_API_ENDPOINT
from django.contrib.auth.models import User
import sys
import os
import redis


class FunctionalTest(StaticLiveServerTestCase):
    """
    Common functional test class which provides the ability to test against a remote server

    use attribute --liveserver=staging.ubuntu.local in with execution to test against a staging server
    """
    download_dir = ""

    @classmethod
    def setUpClass(cls):
        for arg in sys.argv:
            if 'liveserver' in arg:
                cls.server_url = 'http://' + arg.split("=")[1]
                return
        # if no liveserver argument is given, a local test server is used
        super().setUpClass()
        cls.server_url = cls.live_server_url

    @classmethod
    def tearDownClass(cls):
        if cls.server_url == cls.live_server_url:
            super().tearDownClass()

    @staticmethod
    def is_redis_running():
        try:
            rs = redis.Redis("localhost")
            rs.ping()
            return True

        except:
            return False

    def setUp(self):
        self.download_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                         "selenium_downloads")
        print("Selenium Download directory set to %s" % self.download_dir)

        for the_file in os.listdir(self.download_dir):
            file_path = os.path.join(self.download_dir, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as ex:
                print("Failed to delete file, tests may also fail: %s" % ex)

        profile = webdriver.FirefoxProfile()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.manager.showWhenStarting", False)
        profile.set_preference("browser.download.dir", self.download_dir)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")

        self.browser = webdriver.Firefox(firefox_profile=profile)
        self.browser.implicitly_wait(3)

    def tearDown(self):
        self.browser.quit()


@override_settings(APP_CONFIG_FILE="conf/product_database.ft.config")
class DestructiveProductDbFunctionalTest(FunctionalTest):
    API_USERNAME = "api"
    API_PASSWORD = "api"
    ADMIN_USERNAME = "pdb_admin"
    ADMIN_PASSWORD = "pdb_admin"
    TEST_CONFIG_FILE = "conf/product_database.ft.config"

    def clean_config_file(self):
        # cleanup
        if os.path.exists(self.TEST_CONFIG_FILE):
            os.remove(self.TEST_CONFIG_FILE)

    def clean_db(self):
        """
        dropy any usage data form the system, use with care when testing again a live server
        :return:
        """
        drop_all_products(server=self.server_url,
                          username=self.ADMIN_USERNAME,
                          password=self.ADMIN_PASSWORD)

    def handle_login_dialog(self, username, password, expected_content):
        # perform user login with the given credentials
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Login", page_text)

        self.browser.find_element_by_id("username").send_keys(username)
        self.browser.find_element_by_id("password").send_keys(password)
        self.browser.find_element_by_id("login_button").click()
        self.browser.implicitly_wait(3)

        # check that the user sees the expected title
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn(expected_content, page_text, "login failed")

    def create_test_data(self):
        base_path = os.path.join("tests", "data")
        test_data_paths = [
            os.path.join(base_path, "create_cisco_test_data.json"),
            os.path.join(base_path, "create_juniper_test_data.json"),
        ]

        create_real_test_data(server=self.server_url,
                              username=self.ADMIN_USERNAME,
                              password=self.ADMIN_PASSWORD,
                              test_data_paths=test_data_paths)

    def setUp(self):
        super().setUp()
        self.clean_config_file()

        # create superuser
        u = User(username='pdb_admin')
        u.set_password('pdb_admin')
        u.is_superuser = True
        u.is_staff = True
        u.save()
        u = User(username='api')
        u.set_password('api')
        u.email = "api@localhost.localhost"
        u.is_superuser = False
        u.is_staff = False
        u.save()

        self.clean_db()
        self.create_test_data()

        # set API endpoints
        self.PRODUCT_API_URL = self.server_url + PRODUCTS_API_ENDPOINT

    def tearDown(self):
        super().tearDown()
        self.clean_config_file()
