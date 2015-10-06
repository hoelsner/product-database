"""
Unit tests for the Cisco API console
"""
from django.test import TestCase
from app.productdb.extapi import ciscoapiconsole as ciscoapi
from app.productdb.extapi.exception import *
import json
import datetime


class TestInvalidUseOfCiscoApi(TestCase):
    fixtures = ['default_vendors.yaml']

    def setUp(self):
        super().setUp()

    def test_server_unreachable(self):
        try:
            helloapi = ciscoapi.CiscoHelloApi()

            helloapi.client_id = "PlsChgMe"
            helloapi.client_secret = "PlsChgMe"

            # we will change the authentication url to localhost
            helloapi.AUTHENTICATION_URL = "https://localhost/invalid_url"

            helloapi.create_temporary_access_token(force_new_token=True)
            self.fail("load client credentials should fail")

        except ConnectionFailedException as ex:
            self.assertIn('cannot contact authentication server', str(ex))


class TestBasicCiscoApiModule(TestCase):
    """
    verify overall function of the Basic Cisco API class
    """
    fixtures = ['default_vendors.yaml', 'cisco_api_test_credentials.yaml']
    file_with_test_credentials = "ciscoapi.client_credentials.json.bak"

    def test_api_access_using_hello_endpoint(self):
        expected_result = '"response": "Hello World"'

        helloapi = ciscoapi.CiscoHelloApi()

        # you need to manually load the client credentials before working with the API
        helloapi.load_client_credentials()

        helloapi_result = helloapi.hello_api_call()

        self.assertIn(expected_result, json.dumps(helloapi_result))
        print(" - API access working")

        # check that cached token is valid
        self.assertTrue(helloapi.__is_cached_token_valid__(), "cached token should be valid, because if was just "
                                                              "created")

        # check that cached token exists and is loaded correctly
        helloapi2 = ciscoapi.CiscoHelloApi()
        helloapi2.load_client_credentials()

        helloapi2_result = helloapi2.hello_api_call()

        self.assertIn(expected_result, json.dumps(helloapi2_result))
        self.assertFalse(helloapi2.__new_token_created__, "At this point, no new token must be created")

    def test_valid_ready_for_use(self):
        helloapi = ciscoapi.CiscoHelloApi()
        # drop cached token
        helloapi.drop_cached_token()

        # you need to manually load the client credentials before working with the API
        helloapi.load_client_credentials()

        self.assertTrue(helloapi.is_ready_for_use(), "class should be ready to use after this call")

        # after this call the token is cached again (run again to test this state)
        self.assertTrue(helloapi.is_ready_for_use(), "class should be ready to use after this call")

    def test_api_access_with_expired_temp_token_using_hello_endpoint(self):
        expected_result = '"response": "Hello World"'

        helloapi = ciscoapi.CiscoHelloApi()
        helloapi.load_client_credentials()

        helloapi_result = helloapi.hello_api_call()
        self.assertIn(expected_result, json.dumps(helloapi_result))

        helloapi.token_expire_datetime = datetime.datetime.now() - datetime.timedelta(hours=61)
        helloapi_result = helloapi.hello_api_call()

        self.assertIn(expected_result, json.dumps(helloapi_result))
        self.assertTrue(helloapi.__new_token_created__, "Token was programmatic changed to an expired state, "
                                                        "this should not happen")

    def test_save_new_client_credentials(self):
        helloapi = ciscoapi.CiscoHelloApi()
        helloapi.load_client_credentials()

        old_id = helloapi.client_id
        old_secret = helloapi.client_secret
        test_id = "MyTestId"
        test_secret = "MyTestSecret"

        helloapi.client_id = test_id
        helloapi.client_secret = test_secret
        helloapi.save_client_credentials()

        helloapi2 = ciscoapi.CiscoHelloApi()
        helloapi2.load_client_credentials()

        self.assertEquals(helloapi2.client_id, test_id)
        self.assertEquals(helloapi2.client_secret, test_secret)

        helloapi.client_id = old_id
        helloapi.client_secret = old_secret
        helloapi.save_client_credentials()

    def test_invalid_access_token_authentication(self):
        helloapi = ciscoapi.CiscoHelloApi()
        helloapi.load_client_credentials()

        # initial call to populate the class
        helloapi.hello_api_call()

        # modify the access token and see what happens
        wrongkey = "01234567890abcdef"
        helloapi.http_auth_header['Authorization'] = wrongkey

        try:
            # this call will lead to an exception
            helloapi.hello_api_call()
            self.fail('This should not work... authentication without correct access token?')

        except AuthorizationFailedException as ex:
            self.assertIn('Not Authorized', str(ex))
