from rest_framework import status
from tests.base.django_test_cases import DestructiveProductDbFunctionalTest
import tests.base.rest_calls as rest_calls
import json


def extract_dict_a_from_b(A, B):
    return dict(
        [(k, B[k]) for k in A.keys() if k in B.keys()]
    )


class RealDataApiInteraction(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml']

    TEST_PRODUCT_NAME = "WS-C2960X-24PD-L"
    TEST_PRODUCT_LIST_NAME = "Cisco Catalyst 2960X"

    def test_api_get_product_detail_endpoint(self):
        # run multiple times to verify sorting of the list names
        counter = 1
        while counter <= 3:
            apicall = {
                "product_id": self.TEST_PRODUCT_NAME
            }
            # id field omitted, because it may change depending on the database
            expected_list_names = [
                "Cisco Systems",
                "Cisco Catalyst 2960X",
            ]
            expected_list_names.sort()
            expected_result = {
                "product_id": "WS-C2960X-24PD-L",
                "description": "Catalyst 2960-X 24 GigE PoE 370W, 2 x 10G SFP+, LAN Base",
                "list_price": "4595.00",
                "currency": "USD",
                "tags": "chassis",
                "json_data": None,
                "lists": expected_list_names
            }

            response = rest_calls.post_rest_call(api_url=self.PRODUCT_BY_NAME_API_URL,
                                                 data_dict=apicall,
                                                 username=self.API_USERNAME,
                                                 password=self.API_PASSWORD)

            self.assertEqual(response.status_code,
                             status.HTTP_200_OK,
                             "Failed call: %s" % response.content.decode("utf-8"))

            response_json = json.loads(response.content.decode("utf-8"))

            modified_response = extract_dict_a_from_b(expected_result, response_json)
            self.assertSetEqual(set(expected_result), set(modified_response))
            counter += 1
