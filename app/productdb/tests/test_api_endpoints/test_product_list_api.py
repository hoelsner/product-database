"""
Unit tests for ProductList API endpoint
"""
import re
import json

from rest_framework import status

import app.productdb.tests.base.api_endpoints as apiurl
import app.productdb.tests.base.api_test_calls as apicall
from app.productdb.tests import *


class ProductListApiEndpointTest(BaseApiUnitTest):
    fixtures = ['default_vendors.yaml']

    def clean_null_values_from_dict(self, dictionary):
        # remove all None values from the result
        empty_keys = [k for k, v in dictionary.items() if not v]
        for k in empty_keys:
            del dictionary[k]
        return dictionary

    def test_verify_product_list_name_passed(self):
        product_list_names = [
            "Testproduct123400",
            "Testproduct 123400",
            "Testproduct%123400",
            "Testproduct$123400",
            "Testproduct#123400",
            "Testproduct*123400",
        ]

        for product_list_name in product_list_names:
            apicall_data = {
                "product_list_name": product_list_name
            }

            response = self.client.post(apiurl.PRODUCT_LIST_API_ENDPOINT, apicall_data, format='json')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertRegex(response.content.decode("utf-8"),
                             '.*"product_list_name":"%s".*' % re.escape(apicall_data['product_list_name']))
            product_list = json.loads(response.content.decode("utf-8"))

            # verify URL content
            second_call = self.client.get(product_list['url'])
            same_product = json.loads(second_call.content.decode("utf-8"))

            self.assertDictEqual(product_list, same_product)

            # cleanup
            response = self.client.delete(apiurl.PRODUCT_LIST_DETAIL_API_ENDPOINT % product_list['id'])
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content.decode("utf-8"))

        apicall.clean_db(self.client)

    def test_failed_product_list_modify_url(self):
        apicall_data = {
            "product_list_name": "something"
        }

        response = self.client.post(apiurl.PRODUCT_LIST_API_ENDPOINT, apicall_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        product_list = json.loads(response.content.decode("utf-8"))
        url = product_list['url']
        modified_product = product_list
        modified_product['url'] = "http://1.1.1.1/productdb/api/v0/product/123/"
        modified_product = self.clean_null_values_from_dict(modified_product)

        # try to change product url
        response = self.client.put(url, modified_product)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # the URL element is not modified
        result = json.loads(response.content.decode("utf-8"))
        self.assertNotEqual(result['url'], modified_product['url'])

        # cleanup
        response = self.client.delete(apiurl.PRODUCT_LIST_DETAIL_API_ENDPOINT % product_list['id'])
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content.decode("utf-8"))

    def test_unique_constrain_in_product_list_name(self):
        test_product_list_name = "product_list_name"
        apicall_data = {
            "product_list_name": test_product_list_name
        }
        apicall.create_product_list(self.client, test_product_list_name)

        # try to create the product again
        response = self.client.post(apiurl.PRODUCT_LIST_API_ENDPOINT, apicall_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        apicall.result_contains_error(self, STRING_UNIQUE_FIELD_REQUIRED,
                                      "product_list_name",
                                      response.content.decode("utf-8"))

        apicall.clean_db(self.client)

    def test_verify_product_list_name_passed_with_special_characters(self):
        apicall_datas = [
            {"product_list_name": "Testproduct-123400"},
            {"product_list_name": "Testproduct_123400"},
            {"product_list_name": "Testproduct%123400"},
            {"product_list_name": "Testproduct&123400"},
            {"product_list_name": "Testproduct#123400"},
            {"product_list_name": "Testproduct\123400"},
        ]

        for apicall_data in apicall_datas:
            response = self.client.post(apiurl.PRODUCT_LIST_API_ENDPOINT, apicall_data, format='json')

            self.assertEqual(response.status_code,
                             status.HTTP_201_CREATED,
                             "name: %s\ncontent: %s" % (apicall_data, response.content.decode("utf-8")))
            self.assertRegex(response.content.decode("utf-8"),
                             '.*"product_list_name":"%s".*' % apicall_data['product_list_name'])

        apicall.clean_db(self.client)

    def test_valid_byname_api_call(self):
        test_product_list_name = "my_get_name_api_call_test"
        apicall.create_product_list(self.client, test_product_list_name)

        # call getbyname
        valid_apicall = {
            "product_list_name": test_product_list_name
        }
        response = self.client.post(apiurl.PRODUCT_LIST_BY_NAME_API_ENDPOINT, valid_apicall)

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK,
                         "Failed call: %s" % response.content.decode("utf-8"))
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"id":.*"product_list_name":"%s".*' % re.escape(test_product_list_name))
        apicall.clean_db(self.client)

    def test_valid_byname_api_call_with_content_type_json(self):
        test_product_list_name = "my_get_name_api_call_test"
        apicall.create_product_list(self.client, test_product_list_name)

        # call byname
        valid_apicall = {
            "product_list_name": test_product_list_name
        }
        response = self.client.post(apiurl.PRODUCT_LIST_BY_NAME_API_ENDPOINT,
                                    json.dumps(valid_apicall),
                                    content_type="application/json")

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK,
                         "Failed call: %s" % response.content.decode("utf-8"))
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"id":.*"product_list_name":"%s".*' % re.escape(test_product_list_name))

    def test_invalid_byname_api_call(self):
        # call byname
        invalid_apicall = {
            "product_list_name": "not_existing_product_number"
        }
        response = self.client.post(apiurl.PRODUCT_LIST_BY_NAME_API_ENDPOINT, invalid_apicall)

        self.assertEqual(response.status_code,
                         status.HTTP_404_NOT_FOUND,
                         "Failed call: %s" % response.content.decode("utf-8"))
        apicall.result_contains_error(self, STRING_PRODUCT_LIST_NOT_FOUND_MESSAGE % invalid_apicall['product_list_name'],
                                      "product_list_name",
                                      response.content.decode("utf-8"))

    def test_invalid_byname_api_call_with_wrong_apicall_data(self):
        # call byname
        invalid_apicall = {
            "product_lis_name": "not_existing_product_number"
        }
        response = self.client.post(apiurl.PRODUCT_LIST_BY_NAME_API_ENDPOINT, invalid_apicall)

        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST,
                         "Failed call: %s" % response.content.decode("utf-8"))
        apicall.result_contains_error(self, "invalid parameter given, 'product_list_name' required",
                                      "error",
                                      response.content.decode("utf-8"))

    def test_count_api_endpoint(self):
        test_product_list_count = 5
        for i in range(0, test_product_list_count):
            apicall.create_product_list(self.client, "product_list-%04d" % i)

        response = self.client.get(apiurl.PRODUCT_LIST_COUNT_API_ENDPOINT)
        response.content.decode("utf-8")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode("utf-8"),
                         '{"count":%s}' % test_product_list_count)
        apicall.clean_db(self.client)

    def test_valid_namedproducts_api_endpoint(self):
        # create test data
        first_test_product_name = "first_product_name"
        second_test_product_name = "second_product_name"
        test_product_list_name = "product_list_name-01"

        test_product_list = apicall.create_product_list(self.client, test_product_list_name)
        first_product = apicall.create_product(self.client, first_test_product_name)
        second_product = apicall.create_product(self.client, second_test_product_name)

        product_ids = [
            second_product['id'],
            first_product['id'],
        ]
        test_product_list['products'] = product_ids
        apicall.update_product_list(self.client, test_product_list)

        # test named products call
        response = self.client.get(apiurl.PRODUCT_LIST_DETAIL_NAMED_PRODUCTS_API_ENDPOINT % test_product_list['id'])
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content.decode("utf-8"))

        self.assertIn('"products":["%s","%s"]' % (first_test_product_name, second_test_product_name),
                      response.content.decode("utf-8"))

        apicall.clean_db(self.client)

    def test_pagination_defaults(self):
        for i in range(1, 55 + 1):
            apicall_data = {
                "product_list_name": "product_list-%d" % i
            }
            post_response = self.client.post(apiurl.PRODUCT_LIST_API_ENDPOINT, apicall_data, format='json')
            self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)

        res = self.client.get(apiurl.PRODUCT_LIST_API_ENDPOINT)
        self.assertEquals(res.status_code, status.HTTP_200_OK, res.content.decode("utf-8"))
        jres = json.loads(res.content.decode("utf-8"))

        self.assertEquals(jres['pagination']['page'], 1)
        self.assertEquals(jres['pagination']['last_page'], 3)
        self.assertEquals(jres['pagination']['total_records'], 55)
        self.assertEquals(jres['pagination']['page_records'], 25)

        res = self.client.get(apiurl.PRODUCT_LIST_API_ENDPOINT + "?page=2")
        jres = json.loads(res.content.decode("utf-8"))

        self.assertEquals(jres['pagination']['page'], 2)
        self.assertEquals(jres['pagination']['last_page'], 3)
        self.assertEquals(jres['pagination']['total_records'], 55)
        self.assertEquals(jres['pagination']['page_records'], 25)

        res = self.client.get(apiurl.PRODUCT_LIST_API_ENDPOINT + "?page=3")
        jres = json.loads(res.content.decode("utf-8"))

        self.assertEquals(jres['pagination']['page'], 3)
        self.assertEquals(jres['pagination']['last_page'], 3)
        self.assertEquals(jres['pagination']['total_records'], 55)
        self.assertEquals(jres['pagination']['page_records'], 5)

        apicall.clean_db(self.client)

    def test_custom_page_length(self):
        for i in range(1, 55 + 1):
            apicall_data = {
                "product_list_name": "product_list-%d" % i
            }
            post_response = self.client.post(apiurl.PRODUCT_LIST_API_ENDPOINT, apicall_data, format='json')
            self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)

        res = self.client.get(apiurl.PRODUCT_LIST_API_ENDPOINT + "?page_size=15")
        self.assertEquals(res.status_code, status.HTTP_200_OK, res.content.decode("utf-8"))
        jres = json.loads(res.content.decode("utf-8"))

        self.assertEquals(jres['pagination']['page'], 1)
        self.assertEquals(jres['pagination']['last_page'], 4)
        self.assertEquals(jres['pagination']['total_records'], 55)
        self.assertEquals(jres['pagination']['page_records'], 15)

        res = self.client.get(apiurl.PRODUCT_LIST_API_ENDPOINT + "?page_size=15&page=2")
        jres = json.loads(res.content.decode("utf-8"))

        self.assertEquals(jres['pagination']['page'], 2)
        self.assertEquals(jres['pagination']['last_page'], 4)
        self.assertEquals(jres['pagination']['total_records'], 55)
        self.assertEquals(jres['pagination']['page_records'], 15)

        res = self.client.get(apiurl.PRODUCT_LIST_API_ENDPOINT + "?page_size=15&page=4")
        jres = json.loads(res.content.decode("utf-8"))

        self.assertEquals(jres['pagination']['page'], 4)
        self.assertEquals(jres['pagination']['last_page'], 4)
        self.assertEquals(jres['pagination']['total_records'], 55)
        self.assertEquals(jres['pagination']['page_records'], 10)

        apicall.clean_db(self.client)
