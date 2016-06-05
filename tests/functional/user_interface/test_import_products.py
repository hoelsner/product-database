import os
import json
import time

from django.core.urlresolvers import reverse
from rest_framework import status
from tests.base.django_test_cases import DestructiveProductDbFunctionalTest
import tests.base.rest_calls as rest_calls


class TestImportProducts(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml', ]

    def handle_upload_dialog(self, filename, verify_that_file_exists=True):
        if not os.path.isfile(filename) and verify_that_file_exists:
            self.fail("local file for upload not found: %s" % filename)

        self.browser.find_element_by_id("id_excel_file").send_keys(filename)
        self.browser.find_element_by_id("submit_form").click()

    def handle_login_dialog(self, username, password, expected_content):
        # perform user login with the given credentials
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn("Login", page_text)

        self.browser.find_element_by_id("username").send_keys(username)
        self.browser.find_element_by_id("password").send_keys(password)
        self.browser.find_element_by_id("login_button").click()

        # check that the user sees the expected title
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertIn(expected_content, page_text, "Login failed")

    def test_valid_import_product_import_using_the_bundled_excel_template(self):
        # go to the import products page
        self.browser.get(self.server_url + reverse("productdb:import_products"))
        self.browser.implicitly_wait(3)

        # handle the login dialog
        self.handle_login_dialog(self.ADMIN_USERNAME, self.ADMIN_PASSWORD, "Import products")

        # add test excel file to dialog and submit the file
        test_excel_file = os.path.join(os.getcwd(), "tests", "data", "excel_import_products_test.xlsx")
        self.handle_upload_dialog(test_excel_file)

        # the process is not works not asynchron, therefore it takes some time before the results are displayed

        # verify the output of the upload dialog
        expected_title = "You have imported 25 valid products and 0 invalid products."
        expected_contents = [
            "created product WS-C2960S-48FPD-L",
            "created product WS-C2960S-48LPD-L",
            "created product WS-C2960S-24PD-L",
            "created product WS-C2960S-48TD-L",
        ]
        page_content = self.browser.find_element_by_tag_name("body").text
        self.assertIn(expected_title, page_content)
        for c in expected_contents:
            self.assertIn(c, page_content)
        time.sleep(10)

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
        for part in parts:
            apicall = {
                "product_id": part['id']
            }
            # id field omitted, because it may change depending on the database
            response = rest_calls.post_rest_call(api_url=self.PRODUCT_BY_NAME_API_URL,
                                                 data_dict=apicall,
                                                 username=self.ADMIN_USERNAME,
                                                 password=self.ADMIN_PASSWORD)

            self.assertEqual(response.status_code,
                             status.HTTP_200_OK,
                             "Failed call: %s" % response.content.decode("utf-8"))

            response_json = json.loads(response.content.decode("utf-8"))

            modified_response = [(k, response_json[k]) for k in required_keys if k in response_json.keys()]
            print(part['expect'])
            for s in part['expect']:
                self.assertIn(s, set(modified_response))

    def test_invalid_product_import_using_an_excel_file_with_invalid_keys(self):
        # go to the import products page
        self.browser.get(self.server_url + reverse("productdb:import_products"))
        self.browser.implicitly_wait(3)

        # handle the login dialog
        self.handle_login_dialog(self.ADMIN_USERNAME, self.ADMIN_PASSWORD, "Import products")

        # upload an excel file with invalid keys
        test_excel_file = os.path.join(os.getcwd(),
                                       "tests",
                                       "data",
                                       "excel_import_products_test-invalid_keys.xlsx")
        self.handle_upload_dialog(test_excel_file)

        # verify that the correct error message is displayed
        expected_content = "Invalid structure in Excel file (required keys not found in Excel file)"
        page_content = self.browser.find_element_by_tag_name("body").text
        self.assertIn(expected_content, page_content)

    def test_invalid_product_import_using_an_excel_file_with_invalid_table_name(self):
        # go to the import products page
        self.browser.get(self.server_url + reverse("productdb:import_products"))
        self.browser.implicitly_wait(3)

        # handle the login dialog
        self.handle_login_dialog(self.ADMIN_USERNAME, self.ADMIN_PASSWORD, "Import products")

        # upload an excel file with invalid keys
        test_excel_file = os.path.join(os.getcwd(),
                                       "tests",
                                       "data",
                                       "excel_import_products_test-invalid_table_name.xlsx")
        self.handle_upload_dialog(test_excel_file)

        # verify that the correct error message is displayed
        expected_content = "Invalid structure in Excel file (sheet 'products' not found)"
        page_content = self.browser.find_element_by_tag_name("body").text
        self.assertIn(expected_content, page_content)

    def test_invalid_product_import_using_an_invalid_table_name(self):
        # go to the import products page
        self.browser.get(self.server_url + reverse("productdb:import_products"))
        self.browser.implicitly_wait(3)

        # handle the login dialog
        self.handle_login_dialog(self.ADMIN_USERNAME, self.ADMIN_PASSWORD, "Import products")

        # upload an excel file with invalid keys
        test_excel_file = os.path.join(os.getcwd(),
                                       "tests",
                                       "data",
                                       "excel_import_products_test-invalid_table_name.xlsx")
        self.handle_upload_dialog(test_excel_file)

        # verify that the correct error message is displayed
        expected_content = "Invalid structure in Excel file (sheet 'products' not found)"
        page_content = self.browser.find_element_by_tag_name("body").text
        self.assertIn(expected_content, page_content)

    def test_invalid_product_import_using_an_excel_file_that_exceeds_the_limit(self):
        # go to the import products page
        self.browser.get(self.server_url + reverse("productdb:import_products"))
        self.browser.implicitly_wait(3)

        # handle the login dialog
        self.handle_login_dialog(self.ADMIN_USERNAME, self.ADMIN_PASSWORD, "Import products")

        # upload an excel file with invalid keys
        test_excel_file = os.path.join(os.getcwd(),
                                       "tests",
                                       "data",
                                       "excel_import_products_test-invalid_too_large.xlsx")
        self.handle_upload_dialog(test_excel_file)

        # verify that the correct error message is displayed
        expected_content = "Excel files with more than 20000 entries are currently not supported " \
                           "(found 20001 entries), please upload multiple smaller files"
        page_content = self.browser.find_element_by_tag_name("body").text
        self.assertIn(expected_content, page_content)
