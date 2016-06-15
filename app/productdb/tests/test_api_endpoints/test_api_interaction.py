"""
Unit tests for the interaction with the model using the API
"""
from requests.auth import HTTPBasicAuth
from rest_framework import status
import app.productdb.tests.base.api_test_calls as apicalls
import app.productdb.tests.base.api_endpoints as apiurl
from app.productdb.tests import *


class ApiEndpointInteractionTest(BaseApiUnitTest):
    fixtures = ['default_vendors.yaml']

    def test_api_session_login_failed(self):
        # successful login is already tested in the setUp method
        client = APIClient()
        self.assertFalse(client.login(username=self.API_USERNAME, password="invalid_password"))

    def test_api_anonymous_product_read_access(self):
        # create test product
        test_product_id = "product_id"
        product = apicalls.create_product(self.client, test_product_id, self.ADMIN_USERNAME, self.ADMIN_PASSWORD)

        # create new client to force unauthenticated access
        client = APIClient()
        response = client.get(apiurl.PRODUCT_DETAIL_API_ENDPOINT % product['id'])

        self.assertEqual(response.status_code,
                         status.HTTP_401_UNAUTHORIZED,
                         "Failed call: %s" % response.content.decode("utf-8"))
        self.assertIn('"detail":"Authentication credentials were not provided."',
                      response.content.decode("utf-8"))

    def test_api_authenticated_product_write_access(self):
        # create test product
        test_product_id = "product_id"
        product = apicalls.create_product(self.client, test_product_id, self.ADMIN_USERNAME, self.ADMIN_PASSWORD)

        # create new client to force unauthenticated access
        client = APIClient()
        client.login(username=self.API_USERNAME, password=self.API_PASSWORD)
        # perform get operation get using a read-only account
        response = client.get(
            apiurl.PRODUCT_DETAIL_API_ENDPOINT % product['id'],
            format='json'
        )

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK,
                         "Failed call: %s" % response.content.decode("utf-8"))
        self.assertRegex(response.content.decode("utf-8"),
                         r'.*"id":%s,.*' % product['id'])

    def test_api_unauthenticated_write_access(self):
        # create test product
        test_product_id = "product_id"
        product = apicalls.create_product(self.client, test_product_id, self.ADMIN_USERNAME, self.ADMIN_PASSWORD)

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
