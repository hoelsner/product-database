"""
Test suite for the selenium test cases
"""
from urllib import parse
from datetime import datetime
import pytest
import requests
from django.utils.dateformat import DateFormat
from django.utils.formats import get_format
from requests.auth import HTTPBasicAuth

from tests import BaseSeleniumTest, PRODUCTS_API_ENDPOINT


@pytest.mark.online
@pytest.mark.selenium
class TestApiUseCases(BaseSeleniumTest):
    def test_swagger_ui_has_no_500(self, browser, liveserver):
        browser.get(liveserver + "/productdb/api-docs/")

        page_text = browser.find_element_by_tag_name('body').text

        assert "INTERNAL SERVER ERROR" not in page_text, "No internal server error is visible"

    def test_regex_search_on_products_api_endpoint(self, browser, liveserver):
        """
        test regular expression search on API
        """
        self.api_helper.drop_all_data(liveserver)

        # API responds always in UTC timezone
        today_string = DateFormat(datetime.utcnow()).format(get_format("Y-m-d"))

        self.api_helper.create_product(liveserver, product_id="WS-C2960+24TC-LS", vendor_id=1)
        first_product = self.api_helper.create_product(liveserver, product_id="WS-C2960-24TC-L", vendor_id=1)
        second_product = self.api_helper.create_product(liveserver, product_id="WS-C2960+24TC-L", vendor_id=1)
        self.api_helper.create_product(liveserver, product_id="WS-C2960+24TC-S", vendor_id=1)

        expected_result = {
            "pagination": {
                "last_page": 1,
                "page": 1,
                "page_records": 2,
                "total_records": 2,
                "url": {
                    "previous": None,
                    "next": None
                }
            },
            "data": [
                {
                    "currency": "USD",
                    "description": "",
                    "end_of_new_service_attachment_date": None,
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "end_of_sw_maintenance_date": None,
                    "eol_ext_announcement_date": None,
                    "eol_reference_number": None,
                    "eol_reference_url": None,
                    "eox_update_time_stamp": None,
                    "id": second_product["id"],
                    "internal_product_id": None,
                    "lc_state_sync": False,
                    "list_price": None,
                    "list_price_timestamp": None,
                    "product_group": None,
                    "product_id": "WS-C2960+24TC-L",
                    "tags": "",
                    "update_timestamp": today_string,
                    "url": "https://productdbtestinstance/productdb/api/v1/products/%d/" % second_product["id"],
                    "vendor": 1
                },
                {
                    "currency": "USD",
                    "description": "",
                    "end_of_new_service_attachment_date": None,
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "end_of_sw_maintenance_date": None,
                    "eol_ext_announcement_date": None,
                    "eol_reference_number": None,
                    "eol_reference_url": None,
                    "eox_update_time_stamp": None,
                    "id": first_product["id"],
                    "internal_product_id": None,
                    "lc_state_sync": False,
                    "list_price": None,
                    "list_price_timestamp": None,
                    "product_group": None,
                    "product_id": "WS-C2960-24TC-L",
                    "tags": "",
                    "update_timestamp": today_string,
                    "url": "https://productdbtestinstance/productdb/api/v1/products/%d/" % first_product["id"],
                    "vendor": 1
                }
            ]
        }

        # escape string according https://www.ietf.org/rfc/rfc2396.txt
        search_regex = parse.quote_plus("^WS-C2960\+24TC-L$|^WS-C2960-24TC-L$")

        assert search_regex == "%5EWS-C2960%5C%2B24TC-L%24%7C%5EWS-C2960-24TC-L%24"

        response = requests.get(liveserver + PRODUCTS_API_ENDPOINT + "?search=" + search_regex,
                                auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                headers={'Content-Type': 'application/json'},
                                verify=False,
                                timeout=10)

        assert response.ok is True, response.status_code

        data = response.json()

        assert data == expected_result
