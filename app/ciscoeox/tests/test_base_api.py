import datetime
import json
from django.test import TestCase, override_settings
from app.ciscoeox import base_api as ciscoapi
from app.ciscoeox.exception import ConnectionFailedException, AuthorizationFailedException


class TestInvalidUseOfCiscoApi(TestCase):
    fixtures = ['default_vendors.yaml']

    def setUp(self):
        super().setUp()

    def test_server_unreachable(self):
        """
        test the behavior if the Server for the Cisco API is not reachable
        """
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


@override_settings(APP_CONFIG_FILE="conf/product_database.cisco_api_test.config")
class TestBasicCiscoApiModule(TestCase):
    """
    verify function of the Basic Cisco API class
    """
    fixtures = ['default_vendors.yaml']

    def test_api_access_using_hello_endpoint(self):
        """
        Test the Hello API endpoint
        """
        expected_result = '"response": "Hello World"'
        helloapi = ciscoapi.CiscoHelloApi()

        # you need to manually load the client credentials before working with the API
        helloapi.load_client_credentials()
        helloapi_result = helloapi.hello_api_call()

        # check the result and that that cached token is valid
        self.assertIn(expected_result, json.dumps(helloapi_result))
        self.assertTrue(helloapi.__is_cached_token_valid__(), "cached token should be valid, because if was just "
                                                              "created")

        # check that cached token exists and is loaded correctly
        helloapi2 = ciscoapi.CiscoHelloApi()
        helloapi2.load_client_credentials()

        helloapi2_result = helloapi2.hello_api_call()

        self.assertIn(expected_result, json.dumps(helloapi2_result))
        self.assertFalse(helloapi2.__new_token_created__, "At this point, no new token must be created")

    def test_valid_ready_for_use(self):
        """
        test the ready for use method
        """
        helloapi = ciscoapi.CiscoHelloApi()
        helloapi.drop_cached_token()  # drop cached token

        # you need to manually load the client credentials before working with the API
        helloapi.load_client_credentials()

        self.assertTrue(helloapi.is_ready_for_use(), "class should be ready to use after this call")

        # after this call the token is cached again (run again to test this state)
        self.assertTrue(helloapi.is_ready_for_use(), "class should be ready to use after this call")

    def test_api_access_with_expired_temp_token(self):
        """
        test access with an expired authentication token (should be automatically renewed)
        """
        expected_result = '"ErrorDescription": "EOX information does not exist for the following product ID(s): ' \
                          'WS-C2960-24T-S"'

        eox_api = ciscoapi.CiscoEoxApi()
        eox_api.load_client_credentials()

        call_result = eox_api.query_product("WS-C2960-24T-S")
        self.assertIn(expected_result, json.dumps(call_result))

        eox_api.token_expire_datetime = datetime.datetime.now() - datetime.timedelta(hours=61)
        call_result = eox_api.query_product("WS-C2960-24T-S")

        json.dumps(call_result)
        self.assertIn(expected_result, json.dumps(call_result))
        self.assertTrue(eox_api.__new_token_created__, "Token was programmatic changed to an expired state, "
                                                       "this should not happen")

    def test_invalid_access_token_authentication(self):
        eox_api = ciscoapi.CiscoEoxApi()
        eox_api.load_client_credentials()

        # initial call to populate the class
        eox_api.query_product("WS-C2960-24T-S")

        # modify the access token and see what happens
        wrongkey = "01234567890abcdef"
        eox_api.http_auth_header['Authorization'] = wrongkey

        try:
            # this call will lead to an exception
            eox_api.query_product("WS-C2960-24T-S")
            self.fail('This should not work... authentication without correct access token?')

        except AuthorizationFailedException as ex:
            self.assertIn('Not Authorized', str(ex))


@override_settings(APP_CONFIG_FILE="conf/product_database.cisco_api_test.config")
class TestCiscoEoxApiClass(TestCase):
    """
    test the Cisco EoX API classes
    """
    fixtures = ['default_vendors.yaml']

    def test_valid_eox_call_with_single_product_number(self):
        test_product = "WS-C2960-24-S"

        eox_call = ciscoapi.CiscoEoxApi()
        eox_call.load_client_credentials()

        eox_call.query_product(product_id=test_product)
        records = eox_call.get_eox_records()

        # verify, that no error occurred
        self.assertFalse(eox_call.has_error(records[0]))

        # verify result
        self.assertEquals(eox_call.amount_of_total_records(), 1)
        self.assertEquals(eox_call.amount_of_pages(), 1)
        self.assertEquals(eox_call.get_valid_record_count(), 1)
        self.assertEquals(eox_call.get_current_page(), 1)
        self.assertEquals(records[0]['EOLProductID'], "WS-C2960-24-S")

    def test_valid_eox_call_with_multiple_product_number(self):
        test_product = "WS-C2960-*"

        eox_call = ciscoapi.CiscoEoxApi()
        eox_call.load_client_credentials()

        eox_call.query_product(product_id=test_product)
        records = eox_call.get_eox_records()

        # verify, that no error occurred
        self.assertFalse(eox_call.has_error(records[0]))

        # verify result
        self.assertEquals(eox_call.amount_of_total_records(), 47)
        self.assertEquals(eox_call.amount_of_pages(), 1)
        self.assertEquals(eox_call.get_valid_record_count(), 47)
        self.assertEquals(eox_call.get_current_page(), 1)

        # read all product ids
        expected_pids = (
            'WS-C2960-24LT-L-RF',
            'WS-C2960-8TC-L-RF',
            'WS-C2960-24-S-WS',
            'WS-C2960-48TC-L-RF',
            'WS-C2960-24LC-S-WS',
            'WS-C2960-24PC-S-WS',
            'WS-C2960-24LC-S-RF',
            'WS-C2960-8TC-S-RF',
            'WS-C2960-24PC-L',
            'WS-C2960-24TT-L-WS',
            'WS-C2960-24PC-S-RF',
            'WS-C2960-48TT-L-RF',
            'WS-C2960-8TC-S-WS',
            'WS-C2960-8TC-L',
            'WS-C2960-24TC-L',
            'WS-C2960-48TC-S-RF',
            'WS-C2960-24-S',
            'WS-C2960-48PST-L',
            'WS-C2960-24LT-L-WS',
            'WS-C2960-24PC-L-RF',
            'WS-C2960-24LT-L',
            'WS-C2960-24TC-S-RF',
            'WS-C2960-24TC-S-WS',
            'WS-C2960-48TT-S-WS',
            'WS-C2960-48TC-L-WS',
            'WS-C2960-48TT-L',
            'WS-C2960-24-S-RF',
            'WS-C2960-48TT-S-RF',
            'WS-C2960-24TC-L-RF',
            'WS-C2960-48TC-L',
            'WS-C2960-8TC-S',
            'WS-C2960-48PST-S',
            'WS-C2960-24TC-L-WS',
            'WS-C2960-48TC-S',
            'WS-C2960-48TT-L-WS',
            'WS-C2960-48TT-S',
            'WS-C2960-24TT-L-RF',
            'WS-C2960-24PC-S',
            'WS-C2960-8TC-L-WS',
            'WS-C2960-24PC-L-WS',
            'WS-C2960-48TC-S-WS',
            'WS-C2960-24TC-S',
            'WS-C2960-24LC-S',
            'WS-C2960-24TT-L',
            'WS-C2960-48PSTL-RF'
        )

        pid_result_set = set()
        for record in records:
            pid_result_set.add(record['EOLProductID'])

        self.assertSetEqual(pid_result_set, set(expected_pids))

    def test_invalid_eox_call(self):
        test_product = "AAAABBBB"
        error_message = "EOX information does not exist for the following product ID(s):"
        eox_call = ciscoapi.CiscoEoxApi()
        eox_call.load_client_credentials()

        eox_call.query_product(product_id=test_product)
        records = eox_call.get_eox_records()

        # verify, that error occurred
        self.assertTrue(eox_call.has_error(records[0]))
        self.assertIn(error_message, eox_call.get_error_description(records[0]))
        self.assertEquals(eox_call.amount_of_total_records(), 0)
        self.assertEquals(eox_call.amount_of_pages(), 1)
        self.assertEquals(eox_call.get_valid_record_count(), 0)
        self.assertEquals(eox_call.get_current_page(), 1)
