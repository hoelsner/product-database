"""
Unit tests for the Cisco EoX API
"""
from django.test import TestCase, override_settings
from app.productdb.extapi import ciscoapiconsole as ciscoapi


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

        # verfiy, that no error occured
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

        # verfiy, that no error occured
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

        # verfiy, that error occured
        self.assertTrue(eox_call.has_error(records[0]))
        self.assertIn(error_message, eox_call.get_error_description(records[0]))
        self.assertEquals(eox_call.amount_of_total_records(), 0)
        self.assertEquals(eox_call.amount_of_pages(), 1)
        self.assertEquals(eox_call.get_valid_record_count(), 0)
        self.assertEquals(eox_call.get_current_page(), 1)
