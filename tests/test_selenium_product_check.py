"""
Test suite for the selenium test cases
"""
import os
import pytest
import time
from django.core.urlresolvers import reverse
from selenium.webdriver.common.keys import Keys
from tests import BaseSeleniumTest

pytestmark = pytest.mark.django_db
selenium_test = pytest.mark.skipif(not pytest.config.getoption("--selenium"),
                                   reason="need --selenium to run (implicit usage of the --online flag")


@selenium_test
class TestBulkEolCheckFunction(BaseSeleniumTest):
    def test_optional_product_migration_entry(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        # open the new Product Check page
        browser.get(liveserver + reverse("productdb:create-product_check"))
        browser.find_element_by_id("navbar_login").click()

        homepage_message = "New Product Check"
        self.login_user(browser, self.API_USERNAME, self.API_PASSWORD, homepage_message)

        # the page contains a text field, where the product IDs must be entered
        expected_text = "On this page, you can execute a bulk Product check of multiple Products against the local " \
                        "database. Please enter a list of Product IDs in the following text field separated by line " \
                        "breaks, e.g."
        self.wait_for_text_to_be_displayed_in_body_tag(browser, expected_text)
        assert "Migration source" not in browser.find_element_by_tag_name('body').text

        # enable optional product migration source selection
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_user_profile").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "Edit User Profile")

        browser.find_element_by_id("id_choose_migration_source").click()
        browser.find_element_by_id("submit").click()
        time.sleep(3)

        # open the bulk eol check page
        browser.get(liveserver + reverse("productdb:create-product_check"))
        # the page contains a text field, where the product IDs must be entered
        expected_text = "On this page, you can execute a bulk Product check of multiple Products against the local " \
                        "database. Please enter a list of Product IDs in the following text field separated by line " \
                        "breaks, e.g."
        self.wait_for_text_to_be_displayed_in_body_tag(browser, expected_text)
        assert "Migration source" in browser.find_element_by_tag_name('body').text

        # end session
        browser.get(liveserver + reverse("logout"))

    def test_with_valid_query(self, browser, liveserver, test_download_dir):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        # open the new Product Check page
        browser.get(liveserver + reverse("productdb:create-product_check"))

        # the page contains a text field, where the product IDs must be entered
        expected_text = "On this page, you can execute a bulk Product check of multiple Products against the local " \
                        "database. Please enter a list of Product IDs in the following text field separated by line " \
                        "breaks, e.g."
        self.wait_for_text_to_be_displayed_in_body_tag(browser, expected_text)

        # enter the query and submit (whitespace is stripped)
        sample_eol_query = """WS-C2960-24LC-S
                    WS-C2960-24LC-S
                    WS-C2960-24LC-S
        WS-C2960-24LC-S
        WS-C2960-24LT-L
                    WS-C2960-24PC-S

                    WS-C2960X-24PD-L

                    WS-C2960X-24PD-L
                    WS-C2960X-24PD-L
                    MOH
                    WS-C2960-48PST-S
        WS-C2960-24TC-L
        MOH
                    WS-C2960-24TC-S
                    WS-C2960-24TT-L"""
        browser.find_element_by_id("id_name").send_keys("Test")
        browser.find_element_by_id("id_input_product_ids").send_keys(sample_eol_query)
        browser.find_element_by_id("submit").click()

        # verify result within the product summary table
        expected_product_summary_row = "WS-C2960-24LC-S 4 End of Sale,\n" \
                                       "End of New Service Attachment Date,\n" \
                                       "End of SW Maintenance Releases Date,\n" \
                                       "End of Routine Failure Analysis Date No"
        expected_not_found_query = "MOH 2 Not found in Database --- --- ---"

        # test that the Vendor Bulletin is not visible by default
        assert "Vendor Bulletin" not in browser.find_element_by_tag_name("body").text

        table = browser.find_element_by_class_name("table")
        rows = table.find_elements_by_tag_name('tr')

        assert expected_product_summary_row in [row.text for row in rows]
        assert expected_not_found_query in [row.text for row in rows]

        # scroll down
        text_element = browser.find_element_by_class_name("alert-warning")
        browser.execute_script("return arguments[0].scrollIntoView();", text_element)

        # view the Vendor Bulletin
        dt_buttons = browser.find_element_by_class_name("dt-buttons")
        dt_buttons.find_element_by_link_text("show additional columns").click()
        browser.find_element_by_link_text("Vendor Bulletin").click()

        # test CSV download of the result table
        dt_buttons.find_element_by_link_text("CSV").send_keys(Keys.ENTER)
        time.sleep(5)

        # The file should download automatically (firefox is configured this way)

        # verify that the file is a CSV formatted field (with ";" as delimiter)
        # verify that the second line contains a link (not the Bulletin number)
        file = os.path.join(test_download_dir, "product check - Test.csv")
        header_line = "\ufeffProduct ID;Amount;Lifecycle State;Replacement Product ID;Replacement suggested by;" \
                      "Vendor Bulletin;LC auto-sync"
        with open(file, "r", encoding="utf-8") as f:
            content = f.read().splitlines()
            assert header_line == content[0]
            for line in content:
                if "http://www.cisco.com/en/" in line:
                    break
            else:
                # no line matches, test failed
                pytest.fail("expected content not found in file")

        # test that the table view is stored
        browser.execute_script("window.scrollTo(0, 0)")
        time.sleep(1)
        browser.find_element_by_id("_back").click()
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "All Product Checks")
        time.sleep(2)

        # go back to the product check view
        browser.find_element_by_partial_link_text("Test").click()
        time.sleep(5)

        # test that the Vendor Bulletin is still visible (table state should persist)
        assert "Vendor Bulletin" in browser.find_element_by_tag_name("body").text

        # create new product check
        browser.get(liveserver + reverse("productdb:create-product_check"))
        browser.find_element_by_id("id_name").send_keys("Test")
        browser.find_element_by_id("id_input_product_ids").send_keys(sample_eol_query)
        browser.find_element_by_id("submit").click()
        time.sleep(5)

        # the new product check table should be displayed with the default options (without e.g. the Vendor Bulletin)
        assert "Vendor Bulletin" not in browser.find_element_by_tag_name("body").text

    def test_visible_of_product_checks(self, browser, liveserver):
        self.api_helper.drop_all_data(liveserver)
        self.api_helper.load_base_test_data(liveserver)

        anonymous_product_check_name = "Public created Product Check"
        private_product_check = "Private API User Product Check"
        public_product_check = "Public API User Product Check"
        sample_eol_query = """WS-C2960-24LC-S
                    WS-C2960-24LC-S
                    WS-C2960-24LC-S
        WS-C2960-24LC-S
        WS-C2960-24LT-L
                    WS-C2960-24PC-S

                    WS-C2960X-24PD-L

                    WS-C2960X-24PD-L
                    WS-C2960X-24PD-L
                    MOH
                    WS-C2960-48PST-S
        WS-C2960-24TC-L
        MOH
                    WS-C2960-24TC-S
                    WS-C2960-24TT-L"""

        # open the new Product Check page
        browser.get(liveserver + reverse("productdb:create-product_check"))

        browser.find_element_by_id("id_name").send_keys(anonymous_product_check_name)
        browser.find_element_by_id("id_input_product_ids").send_keys(sample_eol_query)
        browser.find_element_by_id("submit").click()
        time.sleep(2)
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "All Product Checks are")

        # verify result
        assert "All Product Checks are deleted every week on Sunday." in browser.find_element_by_tag_name("body").text

        # verify list entries
        browser.get(liveserver + reverse("productdb:list-product_checks"))
        assert anonymous_product_check_name in browser.find_element_by_id("product_check_table").text

        # login as API user
        browser.get(liveserver + reverse("productdb:create-product_check"))
        time.sleep(2)
        browser.find_element_by_id("navbar_login").click()
        time.sleep(2)

        homepage_message = "New Product Check"
        self.login_user(browser, self.API_USERNAME, self.API_PASSWORD, homepage_message)

        # the page contains a text field, where the product IDs must be entered
        expected_text = "On this page, you can execute a bulk Product check of multiple Products against the local " \
                        "database. Please enter a list of Product IDs in the following text field separated by line " \
                        "breaks, e.g."
        self.wait_for_text_to_be_displayed_in_body_tag(browser, expected_text)

        browser.find_element_by_id("id_name").send_keys(private_product_check)
        browser.find_element_by_id("id_input_product_ids").send_keys(sample_eol_query)
        browser.find_element_by_id("submit").click()
        time.sleep(2)
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "All Product Checks are")

        # verify result
        assert "All Product Checks are deleted every week on Sunday." in browser.find_element_by_tag_name("body").text

        # verify list entries
        browser.get(liveserver + reverse("productdb:list-product_checks"))
        assert private_product_check in browser.find_element_by_id("product_check_table").text

        browser.get(liveserver + reverse("productdb:create-product_check"))

        browser.find_element_by_id("id_name").send_keys(public_product_check)
        browser.find_element_by_id("id_input_product_ids").send_keys(sample_eol_query)
        browser.find_element_by_id("id_public_product_check").click()
        browser.find_element_by_id("submit").click()
        time.sleep(2)
        self.wait_for_text_to_be_displayed_in_body_tag(browser, "All Product Checks are")

        # verify result
        assert "All Product Checks are deleted every week on Sunday." in browser.find_element_by_tag_name("body").text

        browser.get(liveserver + reverse("productdb:list-product_checks"))
        assert anonymous_product_check_name in browser.find_element_by_id("product_check_table").text
        assert private_product_check in browser.find_element_by_id("product_check_table").text
        assert public_product_check in browser.find_element_by_id("product_check_table").text

        # logout
        browser.find_element_by_id("navbar_loggedin").click()
        browser.find_element_by_id("navbar_loggedin_logout").click()
        time.sleep(3)

        browser.get(liveserver + reverse("productdb:list-product_checks"))

        # verify table entries
        assert private_product_check not in browser.find_element_by_id("product_check_table").text
        assert anonymous_product_check_name in browser.find_element_by_id("product_check_table").text
        assert public_product_check in browser.find_element_by_id("product_check_table").text

        # login as root (should also see only the public product checks)
        browser.get(liveserver + reverse("productdb:list-product_checks"))
        browser.find_element_by_id("navbar_login").click()
        time.sleep(3)

        homepage_message = "All Product Checks"
        self.login_user(browser, self.ADMIN_USERNAME, self.ADMIN_PASSWORD, homepage_message)

        # verify table entries
        assert private_product_check not in browser.find_element_by_id("product_check_table").text
        assert anonymous_product_check_name in browser.find_element_by_id("product_check_table").text
        assert public_product_check in browser.find_element_by_id("product_check_table").text
