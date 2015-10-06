"""
Unit tests for the interaction with the model using the API
"""
from rest_framework import status

import app.productdb.tests.base.api_test_calls as apicalls
import app.productdb.tests.base.api_endpoints as apiurl
from app.productdb.tests import *


class ApiEndpointInteractionTest(BaseApiUnitTest):
    fixtures = ['default_vendors.yaml']

    def test_api_session_login_failed(self):
        # successful login is already tested in the setUp method
        client = APIClient()
        self.assertFalse(client.login(username=self.USERNAME, password="invalid_password"))

    def test_api_anonymous_product_read_access(self):
        # create test product
        test_product_id = "product_id"
        product = apicalls.create_product(self.client, test_product_id)

        # create new client to force unauthenticated access
        client = APIClient()
        response = client.get(apiurl.PRODUCT_DETAIL_API_ENDPOINT % product['id'], product)

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK,
                         "Failed call: %s" % response.content.decode("utf-8"))
        self.assertRegex(response.content.decode("utf-8"),
                         r'.*"id":1,.*')

    def test_api_anonymous_product_list_read_access(self):
        # create test product
        test_product_list_name = "product_list_name"
        product_list = apicalls.create_product_list(self.client, test_product_list_name)

        # create new client to force unauthenticated access
        client = APIClient()
        response = client.get(apiurl.PRODUCT_LIST_DETAIL_API_ENDPOINT % product_list['id'], product_list)

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK,
                         "Failed call: %s" % response.content.decode("utf-8"))
        self.assertRegex(response.content.decode("utf-8"),
                         r'.*"id":1,.*')

    def test_api_unauthenticated_write_access(self):
        # create test product
        test_product_id = "product_id"
        product = apicalls.create_product(self.client, test_product_id)

        # create new client to force unauthenticated access
        client = APIClient()
        product['description'] = "I will change it :)"
        response = client.put(apiurl.PRODUCT_DETAIL_API_ENDPOINT % product['id'], product)

        self.assertEqual(response.status_code,
                         status.HTTP_401_UNAUTHORIZED,
                         "Failed call: %s" % response.content.decode("utf-8"))
        apicalls.result_contains_error(self,
                                       "Authentication credentials were not provided.",
                                       "detail",
                                       response.content.decode("utf-8"))

    def test_valid_association_of_a_product_to_single_product_list(self):
        test_product_list_name = "product_list-0001"

        # create test products
        products = [
            "product-0001",
            "product-0002",
            "product-0003",
            "product-0004",
            "product-0005",
        ]
        for product_id in products:
            apicalls.create_product(self.client, product_id)

        # create test product lists
        product_list_names = [
            test_product_list_name,
            "product_list-0002",
            "product_list-0003",
        ]
        for product_list_name in product_list_names:
            apicalls.create_product_list(self.client, product_list_name)

        # assign products
        products = [
            "product-0003",
            "product-0001",
            "product-0002",
        ]
        product_ids = []
        for product_id in products:
            product = apicalls.get_product_by_name(self.client, product_id)
            product_ids.append(product['id'])

        # lookup id
        product_list = apicalls.get_product_list_by_name(self.client, test_product_list_name)

        # associate products to product_list
        product_list["products"] = product_ids
        response_json = apicalls.update_product_list(self.client, product_list)

        # verify results
        self.assertEqual(sorted(response_json['products']), sorted(product_ids))
        apicalls.clean_db(self.client)

    def test_valid_association_of_a_product_to_multiple_product_list(self):
        test_product_list_name = "product_list-0001"
        second_test_product_list_name = "product_list-0002"
        test_product_id = "product-0001"

        # create test products
        products = [
            "product-0001",
            "product-0002",
            "product-0003",
            "product-0004",
            "product-0005",
        ]
        for product_id in products:
            apicalls.create_product(self.client, product_id)

        # create test product lists
        product_list_names = [
            test_product_list_name,
            second_test_product_list_name,
            "product_list-0003",
        ]
        for product_list_name in product_list_names:
            apicalls.create_product_list(self.client, product_list_name)

        # assign products
        products = [
            "product-0003",
            test_product_id,
            "product-0002",
        ]
        product_ids = []
        for product_id in products:
            product = apicalls.get_product_by_name(self.client, product_id)
            product_ids.append(product['id'])

        # lookup id
        product_list = apicalls.get_product_list_by_name(self.client, test_product_list_name)
        second_product_list = apicalls.get_product_list_by_name(self.client, second_test_product_list_name)

        # associate products to product_lists
        product_list["products"] = product_ids
        second_product_list['products'] = product_ids
        apicalls.update_product_list(self.client, product_list)
        apicalls.update_product_list(self.client, second_product_list)

        # verify, that the product is associated with both product_lists
        product = apicalls.get_product_by_name(self.client, test_product_id)

        expected_set = {
            second_test_product_list_name,
            test_product_list_name,
        }
        inters_set = set(product['lists']).intersection(expected_set)
        self.assertSetEqual(inters_set, expected_set)

        apicalls.clean_db(self.client)


