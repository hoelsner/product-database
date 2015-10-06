"""
Unit tests for Vendor API endpoint
"""
import json

from rest_framework import status

import app.productdb.tests.base.api_test_calls as apicall
import app.productdb.tests.base.api_endpoints as apiurl
from app.productdb.tests import *


class VendorApiEndpointTest(BaseApiUnitTest):
    fixtures = ['default_vendors.yaml']

    # values from fixture "default_vendors.yaml"
    DEFAULT_VENDORS = [
        {
            'id': 0,
            'name': 'unassigned',
        },
        {
            'id': 1,
            'name': 'Cisco Systems',
        },
        {
            'id': 2,
            'name': 'Juniper Networks',
        },
    ]

    def test_valid_get_vendor_call(self):
        for vendor_dict in self.DEFAULT_VENDORS:
            response = self.client.get(apiurl.VENDOR_DETAIL_API_ENDPOINT % vendor_dict['id'], format='json')

            self.assertEquals(response.status_code, status.HTTP_200_OK)
            vendor = json.loads(response.content.decode("utf-8"))
            self.assertEquals(vendor_dict['id'], vendor['id'])
            self.assertEquals(vendor_dict['name'], vendor['name'])

    def test_invalid_get_vendor_call_with_wrong_id(self):
        response = self.client.get(apiurl.VENDOR_DETAIL_API_ENDPOINT % 1000, format='json')

        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('"detail":"Not found."', response.content.decode("utf-8"))

    def test_valid_by_name_vendor_call(self):
        for vendor_dict in self.DEFAULT_VENDORS:
            response = self.client.post(apiurl.VENDOR_BY_NAME_API_ENDPOINT,
                                        {"name": vendor_dict['name']},
                                        format='json')

            self.assertEquals(response.status_code, status.HTTP_200_OK)
            vendor = json.loads(response.content.decode("utf-8"))
            self.assertEquals(vendor_dict['id'], vendor['id'], "ID not found in response")
            self.assertEquals(vendor_dict['name'], vendor['name'], "name not found in response")

    def test_invalid_by_name_vendor_call_with_wrong_vendor_name(self):
        vendor_name = "not existing vendor"

        response = self.client.post(apiurl.VENDOR_BY_NAME_API_ENDPOINT, {"name": vendor_name}, format='json')

        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('"name":"Vendor name \'not existing vendor\' not found"', response.content.decode("utf-8"))

    def test_invalid_by_name_vendor_call_with_format_error(self):
        vendor_name = "not existing vendor"

        response = self.client.post(apiurl.VENDOR_BY_NAME_API_ENDPOINT,
                                    {"structural error": vendor_name},
                                    format='json')

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('"error":"invalid parameter given, \'name\' required"', response.content.decode("utf-8"))

    def test_verify_delete_not_allowed(self):
        response = self.client.delete(apiurl.VENDOR_DETAIL_API_ENDPOINT % 1, format='json')

        self.assertEquals(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIn('"detail":"Method \\"DELETE\\" not allowed."', response.content.decode("utf-8"))
