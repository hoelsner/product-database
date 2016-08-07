"""
Unit tests for Product API endpoint
"""
from rest_framework import status
from django.utils.html import escape
import app.productdb.tests.base.api_endpoints as apiurl
from app.productdb.models import ProductGroup, Vendor
from app.productdb.tests import *


class ProductGroupApiEndpointTest(BaseApiUnitTest):
    fixtures = ['default_vendors.yaml']

    TEST_DATA = [
        {
            "name": "test1",
            "vendor": Vendor.objects.filter(name="Cisco Systems").first()
        },
        {
            "name": "test2",
            "vendor": Vendor.objects.filter(name="Cisco Systems").first()
        },
        {
            "name": "test3",
        },
        {
            "name": "test4",
            "vendor": Vendor.objects.filter(name="Juniper Networks").first()
        },
        {
            "name": "test5",
        }
    ]

    def setUp(self):
        super().setUp()
        for entity in self.TEST_DATA:
            ProductGroup.objects.create(**entity)

    def test_valid_get_product_group_call(self):
        """
        test the basic GET call functionality of the API
        """
        self.client.login(username=self.API_USERNAME, password=self.API_PASSWORD)

        response = self.client.get(apiurl.PRODUCT_GROUP_API_ENDPOINT, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = response.json()

        # verify that all product groups are in the response (default page size must be > than 5)
        list_names = [e["name"] for e in self.TEST_DATA]
        result_names = [e["name"] for e in result["data"]]
        list_names.sort()
        result_names.sort()
        self.assertListEqual(list_names, result_names)

        # verify that every test data set has a vendor assigned or is "unassigned" (const)
        expected_result = [[e["name"], e["vendor"].id if "vendor" in e.keys() else 0] for e in self.TEST_DATA]
        # a vendor is always supplied by the API
        real_result = [[e["name"], e["vendor"]] for e in result["data"]]

        self.assertListEqual(expected_result, real_result)

    def test_invalid_get_product_group_call_with_wrong_id(self):
        self.client.login(username=self.API_USERNAME, password=self.API_PASSWORD)

        response = self.client.get(apiurl.PRODUCT_GROUP_API_ENDPOINT + "99999/", format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_ensure_django_permissions_on_product_group(self):
        """
        by default, a registered standard user (as the default API user) is not allowed to perform any write action on
        the database and through the API
        """
        apicall_data = {
            "name": "new Cisco List",
            "vendor": 1
        }

        self.client.login(username=self.API_USERNAME, password=self.API_PASSWORD)
        response = self.client.post(apiurl.PRODUCT_GROUP_API_ENDPOINT, apicall_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_product_group_through_api(self):
        apicall_data = {
            "name": "new Cisco List",
            "vendor": 1
        }

        self.client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)
        response = self.client.post(apiurl.PRODUCT_GROUP_API_ENDPOINT, apicall_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        self.assertEqual(ProductGroup.objects.all().count(), len(self.TEST_DATA) + 1)

    def test_verify_delete_of_product_group_through_api(self):
        pg = ProductGroup.objects.create(name="DeleteTest")

        self.client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)

        response = self.client.delete(apiurl.PRODUCT_GROUP_DETAIL_API_ENDPOINT % pg.id)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_product_group_filter_by_id(self):
        """
        test API filter through API using the ID value of the object
        """
        self.client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)
        pg, _ = ProductGroup.objects.get_or_create(name="test1")

        response = self.client.get(apiurl.PRODUCT_GROUP_API_ENDPOINT + "?id=%d" % pg.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        self.assertTrue("data" in data)
        self.assertTrue(data["pagination"]["total_records"] != 0)
        self.assertEqual("test1", data["data"][0]["name"])

    def test_product_group_filter_by_name(self):
        """
        test the filter through the API with the name parameter (exact operation)
        """
        self.client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)

        # verify exact operation (there is no "test" product group in the test data)
        response = self.client.get(apiurl.PRODUCT_GROUP_API_ENDPOINT + "?name=%s" % escape("test"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue("data" in data)
        self.assertEqual(len(data["data"]), 0)

        # now look for a product group that really exists
        response = self.client.get(apiurl.PRODUCT_GROUP_API_ENDPOINT + "?name=%s" % escape("test1"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue("data" in data)
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual("test1", data["data"][0]["name"])

    def test_product_group_filter_by_vendor(self):
        """
        test the filter through the API with the vendor parameter (startswith operation)
        """
        response = self.client.get(apiurl.PRODUCT_GROUP_API_ENDPOINT + "?vendor=%s" % escape("Cisco"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue("data" in data)
        self.assertEqual(len(data["data"]), 2)  # two lists are in the test data

        names = [e["name"] for e in data["data"]]
        expected_names = [e["name"] for e in self.TEST_DATA if "vendor" in e.keys() if e["vendor"].name == "Cisco Systems"]
        names.sort()
        expected_names.sort()

        self.assertListEqual(names, expected_names)

    def test_product_group_search(self):
        """
        test API search by name
        """
        self.client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)

        response = self.client.get(apiurl.PRODUCT_GROUP_API_ENDPOINT + "?search=test")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue("data" in data)

        names = [e["name"] for e in data["data"]]
        expected_names = [e["name"] for e in self.TEST_DATA]
        names.sort()
        expected_names.sort()

        self.assertEqual(5, data["pagination"]["total_records"])
        self.assertListEqual(names, expected_names)
