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
            self.client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)
            response = self.client.get(apiurl.VENDOR_DETAIL_API_ENDPOINT % vendor_dict['id'], format='json')

            self.assertEquals(response.status_code, status.HTTP_200_OK)
            vendor = json.loads(response.content.decode("utf-8"))
            self.assertEquals(vendor_dict['id'], vendor['id'])
            self.assertEquals(vendor_dict['name'], vendor['name'])

    def test_invalid_get_vendor_call_with_wrong_id(self):
        self.client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)
        response = self.client.get(apiurl.VENDOR_DETAIL_API_ENDPOINT % 1000, format='json')

        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('"detail":"Not found."', response.content.decode("utf-8"))

    def test_verify_delete_not_allowed(self):
        self.client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)
        response = self.client.delete(apiurl.VENDOR_DETAIL_API_ENDPOINT % 1, format='json')

        self.assertEquals(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIn('"detail":"Method \\"DELETE\\" not allowed."', response.content.decode("utf-8"))

    def test_vendor_filter_by_id(self):
        """
        call Vendor API endpoint using the id field (exact match required)
        """
        self.client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)

        response = self.client.get(apiurl.VENDOR_API_ENDPOINT + "?id=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue("data" in data)
        self.assertEqual("Cisco Systems", data["data"][0]["name"])

    def test_vendor_filter_by_name(self):
        """
        call Vendor API endpoint using the name field (exact match required)
        """
        self.client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)

        response = self.client.get(apiurl.VENDOR_API_ENDPOINT + "?name=Cisco%20Systems")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue("data" in data)
        self.assertEqual(1, data["pagination"]["total_records"])
        self.assertEqual("Cisco Systems", data["data"][0]["name"])

    def test_product_search(self):
        """
        test the vendor search feature (contains operation on the name field)
        """
        self.client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)

        response = self.client.get(apiurl.VENDOR_API_ENDPOINT + "?search=Systems")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue("data" in data)
        self.assertEqual(1, data["pagination"]["total_records"])
        self.assertEqual("Cisco Systems", data["data"][0]["name"])
