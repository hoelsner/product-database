"""
Unit tests for Product API endpoint
"""
import re
import json

from rest_framework import status

import app.productdb.tests.base.api_test_calls as apicalls
import app.productdb.tests.base.api_endpoints as apiurl
from app.productdb.tests import *


class ProductApiEndpointTest(BaseApiUnitTest):
    fixtures = ['default_vendors.yaml']

    @staticmethod
    def clean_null_values_from_dict(dictionary):
        # remove all None values from the result
        empty_keys = [k for k, v in dictionary.items() if not v]
        for k in empty_keys:
            del dictionary[k]
        return dictionary

    def test_valid_product_names(self):
        product_names = [
            "Testproduct1234500",
            "Testproduct 1234500",
            "Testproduct#1234500",
            "Testproduct+1234500",
            "Testproduct/1234500",
            "Testproduct%1234500",
            "Testproduct-1234500",
            "Testproduct.1234500",
            "Tes tpa%rt.12345 00#+/-",
        ]

        for product_name in product_names:
            apicall_data = {
                "product_id": product_name
            }

            post_response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')

            self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)
            self.assertRegex(post_response.content.decode("utf-8"),
                             '.*"product_id":"%s".*' % re.escape(apicall_data['product_id']))
            self.assertRegex(post_response.content.decode("utf-8"),
                             '.*"vendor":%d.*' % 0)

            # vendor id field sometimes json decoded as string, sometimes as integer when parsing the post result
            # not a big deal, but better to get the object again to clarify the output
            product = json.loads(post_response.content.decode("utf-8"))
            get_response = self.client.get(apiurl.PRODUCT_DETAIL_API_ENDPOINT % product['id'], format='json')
            product = json.loads(get_response.content.decode("utf-8"))

            # verify URL content
            second_call = self.client.get(product['url'], format='json')
            same_product = json.loads(second_call.content.decode("utf-8"))

            self.assertEqual(product['vendor'], same_product['vendor'],
                             "First call:\n%s\nSecond Call:\n%s\n" % (get_response.content.decode("utf-8"),
                                                                      second_call.content.decode("utf-8")))
            self.assertEqual(json.dumps(product, indent=4), json.dumps(same_product, indent=4))

            # cleanup
            response = self.client.delete(apiurl.PRODUCT_DETAIL_API_ENDPOINT % product['id'])
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content.decode("utf-8"))

        apicalls.clean_db(self.client)

    def test_failed_product_modify_url(self):
        apicall_data = {
            "product_id": "something"
        }

        response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        product = json.loads(response.content.decode("utf-8"))
        url = product['url']
        modified_product = product
        modified_product['url'] = "http://1.1.1.1/productdb/api/v0/product/123/"
        modified_product = self.clean_null_values_from_dict(modified_product)

        # try to change product url
        response = self.client.put(url, modified_product)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # the URL element is not modified
        result = json.loads(response.content.decode("utf-8"))
        self.assertNotEqual(result['url'], modified_product['url'])

        # cleanup
        response = self.client.delete(apiurl.PRODUCT_DETAIL_API_ENDPOINT % product['id'])
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content.decode("utf-8"))

    def test_unique_constrain_in_product_name(self):
        test_product_name = "MyProductName"
        apicall_data = {
            "product_id": test_product_name
        }
        apicalls.create_product(self.client, "MyProductName")

        # try to create the product again
        response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        apicalls.result_contains_error(self,
                                       STRING_UNIQUE_FIELD_REQUIRED,
                                       "product_id",
                                       response.content.decode("utf-8"))

        # cleanup
        apicalls.clean_db(self.client)

    def test_vendor_default_assignment_to_unassigned(self):
        test_product_name = "test_vendor_default_assignment_to_unassigned"
        apicall_data = {
            "product_id": test_product_name
        }
        apicalls.create_product(self.client, "MyProductName")

        # try to create the product again
        response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content.decode("utf-8"))
        self.assertEquals("0",
                          str(json.loads(response.content.decode("utf-8"))['vendor']),
                          response.content.decode("utf-8"))

        # cleanup
        apicalls.clean_db(self.client)

    def test_create_with_default_vendors(self):
        # ID values from fixture "default_vendors.yaml"
        default_vendors = [
            {
                'id': '0',
                'name': 'unassigned',
            },
            {
                'id': '1',
                'name': 'Cisco Systems',
            },
            {
                'id': '2',
                'name': 'Juniper Networks',
            },
        ]
        for i in range(0, len(default_vendors)):
            apicall_data = {
                "product_id": "product-%04d" % i,
                "vendor": default_vendors[i]['id']
            }

            response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertRegex(response.content.decode("utf-8"),
                             '.*"vendor":%s.*' % re.escape(default_vendors[i]['id']))

        # cleanup
        apicalls.clean_db(self.client)

    def test_invalid_create_product_call_with_vendor_id(self):
        test_product_name = "MyProductName"
        apicall_data = {
            "product_id": test_product_name,
            "vendor": 100000
        }
        response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(r'"vendor":["Invalid pk \"100000\" - object does not exist."',
                      response.content.decode("utf-8"))

        # cleanup
        apicalls.clean_db(self.client)

    def test_invalid_product_call_with_vendor_string(self):
        test_product_name = "MyProductName"
        apicall_data = {
            "product_id": test_product_name,
            "vendor": "Invalid Vendor value"
        }
        response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(r'"vendor":["Incorrect type. Expected pk value, received str."]',
                      response.content.decode("utf-8"))

        # cleanup
        apicalls.clean_db(self.client)

    def test_create_product_default_string_in_description_field(self):
        product_name = "description_field_test"

        product = apicalls.create_product(self.client, product_name)
        self.assertEqual(product['description'], "not set")

        apicalls.clean_db(self.client)

    def test_create_product_default_string_in_currency_field(self):
        product_name = "currency_field_test"

        product = apicalls.create_product(self.client, product_name)
        self.assertEqual(product['currency'], "USD")

        apicalls.clean_db(self.client)

    def test_create_product_custom_string_in_currency_field(self):
        product_name = "currency_field_test"

        product = apicalls.create_product(self.client, product_name)
        product['currency'] = "EUR"

        product = apicalls.update_product(self.client, product_dict=product)
        self.assertEqual(product['currency'], "EUR")

        apicalls.clean_db(self.client)

    def test_create_product_with_invalid_string_in_currency_field(self):
        product_name = "currency_field_test"

        product = apicalls.create_product(self.client, product_name)
        product['currency'] = "INV"

        # try to create the product again
        response = self.client.put(apiurl.PRODUCT_DETAIL_API_ENDPOINT % product['id'],
                                   product,
                                   format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        apicalls.result_contains_error(self,
                                       STRING_PRODUCT_INVALID_CURRENCY_VALUE % product['currency'],
                                       "currency",
                                       response.content.decode("utf-8"))

        # cleanup
        apicalls.clean_db(self.client)

    def test_create_with_valid_lifecycle_dates(self):
        apicall_data = {
            "product_id": "test_create_with_valid_lifecycle_dates",
            "eox_update_time_stamp": "2015-01-23",
            "end_of_sale_date": "2014-01-31",
            "end_of_support_date": "2019-01-31",
            "eol_ext_announcement_date": "2013-01-31",
            "end_of_sw_maintenance_date": "2015-01-31",
            "end_of_routine_failure_analysis": "2015-01-31",
            "end_of_service_contract_renewal": "2019-01-29",
            "end_of_new_service_attachment_date": "2015-01-31",
            "eol_reference_number": "EOL9449",
            "eol_reference_url": "http://www.cisco.com/en/US/prod/collateral/switches/ps5718/ps6406/eos-eol-notice-c51-730121.html",
        }

        response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content.decode("utf-8"))
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"product_id":"%s".*' % apicall_data['product_id'])
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"eox_update_time_stamp":"%s".*' % apicall_data['eox_update_time_stamp'])
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"end_of_support_date":"%s".*' % apicall_data['end_of_support_date'])
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"eol_ext_announcement_date":"%s".*' % apicall_data['eol_ext_announcement_date'])
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"end_of_sw_maintenance_date":"%s".*' % apicall_data['end_of_sw_maintenance_date'])
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"end_of_routine_failure_analysis":"%s".*' % apicall_data['end_of_routine_failure_analysis'])
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"end_of_service_contract_renewal":"%s".*' % apicall_data['end_of_service_contract_renewal'])
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"end_of_new_service_attachment_date":"%s".*' %
                         apicall_data['end_of_new_service_attachment_date'])
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"eol_reference_number":"%s".*' % apicall_data['eol_reference_number'])
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"eol_reference_url":"%s".*' % apicall_data['eol_reference_url'])

        apicalls.clean_db(self.client)

    def test_create_with_valid_lifecycle_dates_and_null_value(self):
        apicall_data = {
            "product_id": "test_create_with_valid_lifecycle_dates_and_null_value",
            "eol_reference_number": "EOL9449",
            "eol_reference_url": "http://www.cisco.com/en/US/prod/collateral/switches/ps5718/ps6406/eos-eol-notice-c51-730121.html",
        }

        response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content.decode("utf-8"))
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"product_id":"%s".*' % apicall_data['product_id'])
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"eox_update_time_stamp":%s.*' % "null")
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"end_of_support_date":%s.*' % "null")
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"eol_ext_announcement_date":%s.*' % "null")
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"end_of_sw_maintenance_date":%s.*' % "null")
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"end_of_routine_failure_analysis":%s.*' % "null")
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"end_of_service_contract_renewal":%s.*' % "null")
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"end_of_new_service_attachment_date":%s.*' % "null")
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"eol_reference_number":"%s".*' % apicall_data['eol_reference_number'])
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"eol_reference_url":"%s".*' % apicall_data['eol_reference_url'])

        apicalls.clean_db(self.client)

    def test_create_with_invalid_lifecycle_dates(self):
        apicall_data = {
            "product_id": "test_create_with_invalid_lifecycle_dates",
            "eox_update_time_stamp": "17.01.23",
            "end_of_sale_date": "2014-01-1",
            "end_of_support_date": "2019-16-31",
            "eol_ext_announcement_date": "013-01-31",
            "end_of_sw_maintenance_date": "-1-31",
            "end_of_routine_failure_analysis": "01-31-2015",
            "end_of_service_contract_renewal": "2019-01-49",
            "end_of_new_service_attachment_date": "15-21-31",
            "eol_reference_number": "EOL9449",
            "eol_reference_url": "http://www.cisco.com/en/US/prod/collateral/switches/ps5718/ps6406/eos-eol-notice-c51-730121.html",
        }

        response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')

        date_error = '["Date has wrong format. Use one of these formats instead: YYYY[-MM[-DD]]."]'
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content.decode("utf-8"))
        self.assertIn('"eox_update_time_stamp":%s' % date_error, response.content.decode("utf-8"))
        self.assertIn('"end_of_support_date":%s' % date_error, response.content.decode("utf-8"))
        self.assertIn('"eol_ext_announcement_date":%s' % date_error, response.content.decode("utf-8"))
        self.assertIn('"end_of_sw_maintenance_date":%s' % date_error, response.content.decode("utf-8"))
        self.assertIn('"end_of_routine_failure_analysis":%s' % date_error, response.content.decode("utf-8"))
        self.assertIn('"end_of_service_contract_renewal":%s' % date_error, response.content.decode("utf-8"))
        self.assertIn('"end_of_new_service_attachment_date":%s' % date_error, response.content.decode("utf-8"))

        apicalls.clean_db(self.client)

    def test_update_with_null_value_list_price_string(self):
        product_name = "list_price"

        product = apicalls.create_product(self.client, product_name)
        self.assertEqual(product['list_price'], None)

        # remove all None values from the result
        product = self.clean_null_values_from_dict(product)

        # null value in list price will lead to an 400 error
        product['list_price'] = None
        response = self.client.put(apiurl.PRODUCT_DETAIL_API_ENDPOINT % product['id'], product, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content.decode("utf-8"))

        # null value in list price data without format = json will lead to a 400 with a validation error
        product['list_price'] = None
        response = self.client.put(apiurl.PRODUCT_DETAIL_API_ENDPOINT % product['id'], product)

        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST,
                         response.content.decode("utf-8"))
        apicalls.result_contains_error(self,
                                       STRING_LIST_PRICE_VERIFICATION_FAILED,
                                       "list_price",
                                       response.content.decode("utf-8"))

        apicalls.clean_db(self.client)

    def test_create_with_valid_list_price(self):
        """
        Valid list price values for POST
        :return:
        """
        list_prices = [
            ['100', '"100.00"'],
            ['150.00', '"150.00"'],
            ['1150.00', '"1150.00"'],
            ['0', '"0.00"'],
            ['', 'null'],
        ]
        count = 1
        for list_price in list_prices:
            if list_price[0] == "":
                # test result of empty call
                apicall_data = {
                    "product_id": "product_with_%04d" % count,
                }
            else:
                apicall_data = {
                    "product_id": "product_with_%04d" % count,
                    "list_price": list_price[0]
                }

            response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')

            self.assertEqual(response.status_code,
                             status.HTTP_201_CREATED,
                             "Failed: %s\nwith\n%s" % (list_price[0], response.content.decode("utf-8")))
            verify_regex = '.*"product_id":"%s".*"list_price":%s.*' % (apicall_data['product_id'], list_price[1])
            self.assertRegex(response.content.decode("utf-8"),
                             verify_regex,
                             "Failed with\n%s" % response.content.decode("utf-8"))
            count += 1

        apicalls.clean_db(self.client)

    def test_create_with_invalid_list_price(self):
        """
        Test invalid list prices in POST statement
        :return:
        """
        list_prices = [
            "1oo",
            "1OO",
            "100,00",
            "12ff",
        ]

        for list_price in list_prices:
            apicall_data = {
                "product_id": "invalid_element",
                "list_price": list_price
            }

            response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')

            self.assertEqual(response.status_code,
                             status.HTTP_400_BAD_REQUEST,
                             "Failed: %s\n with\n%s" % (list_price, response.content.decode("utf-8")))
            apicalls.result_contains_error(self,
                                           STRING_LIST_PRICE_VERIFICATION_FAILED,
                                           "list_price", response.content.decode("utf-8"))

    def test_create_with_invalid_negative_value_in_list_price(self):
        """
        Test failure on negative values in list prices in POST statement
        :return:
        """
        list_prices = [
            "-100.00",
            "-100",
            "-1"
        ]

        for list_price in list_prices:
            apicall_data = {
                "product_id": "invalid_element",
                "list_price": list_price
            }

            response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')

            self.assertEqual(response.status_code,
                             status.HTTP_400_BAD_REQUEST,
                             "Failed: %s\n with\n%s" % (list_price, response.content.decode("utf-8")))
            apicalls.result_contains_error(self,
                                           STRING_LIST_PRICE_GREATER_OR_EQUAL_ZERO,
                                           "list_price", response.content.decode("utf-8"))

    def test_valid_byname_api_call(self):
        test_product_name = "my_get_name_api_call_test"
        apicalls.create_product(self.client, test_product_name)

        # call byname api endpoint
        valid_apicall = {
            "product_id": test_product_name
        }
        response = self.client.post(apiurl.PRODUCT_BY_NAME_API_ENDPOINT, valid_apicall)

        # verify results
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK,
                         "Failed call: %s" % response.content.decode("utf-8"))
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"id":.*"product_id":"%s".*' % re.escape(valid_apicall['product_id']))

        apicalls.clean_db(self.client)

    def test_valid_byname_api_call_with_content_type_json(self):
        test_product_name = "my_get_name_api_call_test"
        apicalls.create_product(self.client, test_product_name)

        # call byname
        valid_apicall = {
            "product_id": test_product_name
        }
        response = self.client.post(apiurl.PRODUCT_BY_NAME_API_ENDPOINT,
                                    json.dumps(valid_apicall),
                                    content_type="application/json")

        # verify result
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK,
                         "Failed call: %s" % response.content.decode("utf-8"))
        self.assertRegex(response.content.decode("utf-8"),
                         '.*"id":.*"product_id":"%s".*' % re.escape(valid_apicall['product_id']))

        apicalls.clean_db(self.client)

    def test_invalid_byname_api_call_with_wrong_apicall_data_format(self):
        # call byname
        invalid_apicall = {
            "pa_name": "not_existing_product_number"
        }
        response = self.client.post(apiurl.PRODUCT_BY_NAME_API_ENDPOINT, invalid_apicall)

        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST,
                         "Failed call: %s" % response.content.decode("utf-8"))
        apicalls.result_contains_error(self, "invalid parameter given, 'product_id' required",
                                       "error",
                                       response.content.decode("utf-8"))

    def test_invalid_getbyname_api_call(self):
        # call byname
        invalid_apicall = {
            "product_id": "not_existing_product_number"
        }
        response = self.client.post(apiurl.PRODUCT_BY_NAME_API_ENDPOINT, invalid_apicall)

        self.assertEqual(response.status_code,
                         status.HTTP_404_NOT_FOUND,
                         "Failed call: %s" % response.content.decode("utf-8"))
        apicalls.result_contains_error(self, STRING_PRODUCT_NOT_FOUND_MESSAGE % invalid_apicall['product_id'],
                                       "product_id",
                                       response.content.decode("utf-8"))

    def test_count_api_endpoint(self):
        test_data_count = 5
        for i in range(0, test_data_count):
            apicalls.create_product(self.client, "test_count-product_%04d" % i)

        #
        response = self.client.get(apiurl.PRODUCT_COUNT_API_ENDPOINT)
        response.content.decode("utf-8")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode("utf-8"),
                         '{"count":%s}' % test_data_count)
        apicalls.clean_db(self.client)

    def test_product_pagination_defaults(self):
        for i in range(1, 55 + 1):
            apicall_data = {
                "product_id": "product-%d" % i
            }
            post_response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')
            self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)

        res = self.client.get(apiurl.PRODUCT_API_ENDPOINT)
        self.assertEquals(res.status_code, status.HTTP_200_OK, res.content.decode("utf-8"))
        jres = json.loads(res.content.decode("utf-8"))

        self.assertEquals(jres['pagination']['page'], 1)
        self.assertEquals(jres['pagination']['last_page'], 3)
        self.assertEquals(jres['pagination']['total_records'], 55)
        self.assertEquals(jres['pagination']['page_records'], 25)

        res = self.client.get(apiurl.PRODUCT_API_ENDPOINT + "?page=2")
        jres = json.loads(res.content.decode("utf-8"))

        self.assertEquals(jres['pagination']['page'], 2)
        self.assertEquals(jres['pagination']['last_page'], 3)
        self.assertEquals(jres['pagination']['total_records'], 55)
        self.assertEquals(jres['pagination']['page_records'], 25)

        res = self.client.get(apiurl.PRODUCT_API_ENDPOINT + "?page=3")
        jres = json.loads(res.content.decode("utf-8"))

        self.assertEquals(jres['pagination']['page'], 3)
        self.assertEquals(jres['pagination']['last_page'], 3)
        self.assertEquals(jres['pagination']['total_records'], 55)
        self.assertEquals(jres['pagination']['page_records'], 5)

        apicalls.clean_db(self.client)

    def test_product_custom_page_length(self):
        for i in range(1, 55 + 1):
            apicall_data = {
                "product_id": "product-%d" % i
            }
            post_response = self.client.post(apiurl.PRODUCT_API_ENDPOINT, apicall_data, format='json')
            self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)

        res = self.client.get(apiurl.PRODUCT_API_ENDPOINT + "?page_size=15")
        self.assertEquals(res.status_code, status.HTTP_200_OK, res.content.decode("utf-8"))
        jres = json.loads(res.content.decode("utf-8"))

        self.assertEquals(jres['pagination']['page'], 1)
        self.assertEquals(jres['pagination']['last_page'], 4)
        self.assertEquals(jres['pagination']['total_records'], 55)
        self.assertEquals(jres['pagination']['page_records'], 15)

        res = self.client.get(apiurl.PRODUCT_API_ENDPOINT + "?page_size=15&page=2")
        jres = json.loads(res.content.decode("utf-8"))

        self.assertEquals(jres['pagination']['page'], 2)
        self.assertEquals(jres['pagination']['last_page'], 4)
        self.assertEquals(jres['pagination']['total_records'], 55)
        self.assertEquals(jres['pagination']['page_records'], 15)

        res = self.client.get(apiurl.PRODUCT_API_ENDPOINT + "?page_size=15&page=4")
        jres = json.loads(res.content.decode("utf-8"))

        self.assertEquals(jres['pagination']['page'], 4)
        self.assertEquals(jres['pagination']['last_page'], 4)
        self.assertEquals(jres['pagination']['total_records'], 55)
        self.assertEquals(jres['pagination']['page_records'], 10)

        apicalls.clean_db(self.client)
