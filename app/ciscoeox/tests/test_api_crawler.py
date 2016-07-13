import json
import os
from datetime import datetime
from django.test import TestCase
from django.test import override_settings
from app.ciscoeox import api_crawler
from app.ciscoeox.api_crawler import update_cisco_eox_database
from app.ciscoeox.tasks import execute_task_to_synchronize_cisco_eox_states
from app.config import AppSettings
from app.productdb.models import Product, Vendor


class BaseCiscoEoxTestCase(TestCase):
    CONFIG_FILE = ""

    def setUp(self):
        """
        read the Cisco API credentials from the user configuration file and use them for the test case
        """
        ciscred = AppSettings()
        ciscred.CONFIG_FILE_NAME = "conf/product_database.cisco_api_test.config"
        ciscred.read_file()

        client_id = ciscred.get_cisco_api_client_id()
        client_secret = ciscred.get_cisco_api_client_secret()

        appconfig = AppSettings()
        appconfig.read_file()

        appconfig.set_cisco_api_client_id(client_id)
        appconfig.set_cisco_api_client_secret(client_secret)

        appconfig.write_file()

    def tearDown(self):
        super(BaseCiscoEoxTestCase, self).tearDown()
        # cleanup
        if os.path.exists(self.CONFIG_FILE):
            os.remove(self.CONFIG_FILE)

    def update_config_file(self, blacklist, autocreate, queries=""):
        """
        Update the test application configuration file
        """
        appconfig = AppSettings()
        appconfig.read_file()

        appconfig.set_cisco_api_enabled(True)
        appconfig.set_cisco_eox_api_queries(queries)
        appconfig.set_product_blacklist_regex(blacklist)
        appconfig.set_auto_create_new_products(autocreate)

        appconfig.write_file()


@override_settings(APP_CONFIG_FILE="conf/test.TestCiscoEoxCrawler.config")
class TestCiscoEoxDatabaseUpdate(TestCase):
    fixtures = ['default_vendors.yaml']

    def tearDown(self):
        super(TestCiscoEoxDatabaseUpdate, self).tearDown()
        # cleanup
        if os.path.exists("conf/test.TestCiscoEoxCrawler.config"):
            os.remove("conf/test.TestCiscoEoxCrawler.config")

    def test_eox_update_call_with_sample_data(self):
        app_config = AppSettings()
        app_config.read_file()

        app_config.set_cisco_api_enabled(True)
        app_config.set_periodic_sync_enabled(True)
        app_config.write_file()

        eox_sample_response = os.path.join("app",
                                           "ciscoeox",
                                           "tests",
                                           "cisco_eox_sample_response.json")
        eox_db_json = json.loads(open(eox_sample_response).read())

        for record in eox_db_json['EOXRecord']:
            api_crawler.update_local_db_based_on_record(record, True)

    def test_eox_update_call_with_special_character(self):
        """
        test, that no issue exists when the '%' sign is present in the ProductID
        :return:
        """
        app_config = AppSettings()
        app_config.read_file()

        app_config.set_cisco_api_enabled(True)
        app_config.set_periodic_sync_enabled(True)
        app_config.write_file()

        eox_db_record = """{
            "EndOfServiceContractRenewal": {
                "value": " ",
                "dateFormat": "YYYY-MM-DD"
            },
            "ProductIDDescription": "^IPX 8 CDP W/E1EC TO UNIVERSAL CDP (IPX 8/16/32)",
            "ProductBulletinNumber": "LEGACY_ESC_IPX_4",
            "LastDateOfSupport": {
                "value": "2003-07-01",
                "dateFormat": "YYYY-MM-DD"
            },
            "EOXInputValue": "SPA* ",
            "EOLProductID": "SPARE%",
            "UpdatedTimeStamp": {
                "value": "2015-08-23",
                "dateFormat": "YYYY-MM-DD"
            },
            "EOXInputType": "ShowEOXByPids",
            "EndOfRoutineFailureAnalysisDate": {
                "value": " ",
                "dateFormat": "YYYY-MM-DD"
            },
            "LinkToProductBulletinURL": "http://www.cisco.com/en/US/products/hw/tsd_products_support_end-of-sale_and_end-of-life_products_list.html",
            "EndOfSvcAttachDate": {
                "value": " ",
                "dateFormat": "YYYY-MM-DD"
            },
            "EndOfSaleDate": {
                "value": "1998-07-02",
                "dateFormat": "YYYY-MM-DD"
            },
            "EndOfSWMaintenanceReleases": {
                "value": " ",
                "dateFormat": "YYYY-MM-DD"
            },
            "EOXExternalAnnouncementDate": {
                "value": "1998-01-03",
                "dateFormat": "YYYY-MM-DD"
            },
            "EOXMigrationDetails": {
                "MigrationStrategy": " ",
                "MigrationProductId": " ",
                "MigrationProductInfoURL": " ",
                "PIDActiveFlag": "Y  ",
                "MigrationProductName": "See Product Bulletin",
                "MigrationInformation": " ",
                "MigrationOption": "Enter Product Name(s)"
            }
        }"""
        eox_db_json = json.loads(eox_db_record)
        api_crawler.update_local_db_based_on_record(eox_db_json, True)

        _ = Product.objects.get(product_id="SPARE%")

    def test_valid_eox_call_with_create_missing(self):
        test_product = "WS-C3560C-8PC-S"

        sample_record = """{
            "EndOfSvcAttachDate": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2017-06-30"
            },
            "EndOfServiceContractRenewal": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2021-01-28"
            },
            "ProductBulletinNumber": "EOL10691",
            "EOLProductID": "WS-C3560C-8PC-S",
            "LinkToProductBulletinURL": "http://www.cisco.com/c/en/us/products/collateral/switches/catalyst-3560-c-series-switches/eos-eol-notice-c51-736180.html",
            "EOXExternalAnnouncementDate": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2015-10-31"
            },
            "UpdatedTimeStamp": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2015-11-03"
            },
            "EOXMigrationDetails": {
                "MigrationProductInfoURL": "http://www.cisco.com/c/en/us/products/switches/catalyst-3560-cx-series-switches/index.html",
                "PIDActiveFlag": "Y  ",
                "MigrationStrategy": " ",
                "MigrationProductName": " ",
                "MigrationProductId": "WS-C3560CX-8PC-S",
                "MigrationOption": "Enter PID(s)",
                "MigrationInformation": "Cisco Catalyst 3560-CX 8 Port PoE IP Base"
            },
            "EndOfRoutineFailureAnalysisDate": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2017-10-15"
            },
            "EOXInputType": "ShowEOXByPids",
            "EndOfSaleDate": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2016-10-30"
            },
            "EndOfSWMaintenanceReleases": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2017-10-30"
            },
            "EndOfSecurityVulSupportDate": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2017-11-30"
            },
            "EOXInputValue": "WS-C3560C-8PC-S ",
            "LastDateOfSupport": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2025-10-31"
            },
            "ProductIDDescription": "Catalyst 3560C Switch 8 FE PoE, 2 x Dual Uplink, IP Base"
        }"""

        eox_db_json = json.loads(sample_record)
        api_crawler.update_local_db_based_on_record(eox_db_json, create_missing=True)

        p = Product.objects.get(product_id=test_product)

        self.assertEqual(p.eox_update_time_stamp.strftime("%Y-%m-%d"), "2015-11-03")
        self.assertEqual(p.end_of_sale_date.strftime("%Y-%m-%d"), "2016-10-30")
        self.assertEqual(p.eol_ext_announcement_date.strftime("%Y-%m-%d"), "2015-10-31")
        self.assertEqual(p.end_of_sw_maintenance_date.strftime("%Y-%m-%d"), "2017-10-30")
        self.assertEqual(p.end_of_routine_failure_analysis.strftime("%Y-%m-%d"), "2017-10-15")
        self.assertEqual(p.end_of_service_contract_renewal.strftime("%Y-%m-%d"), "2021-01-28")
        self.assertEqual(p.end_of_new_service_attachment_date.strftime("%Y-%m-%d"), "2017-06-30")
        self.assertEqual(p.end_of_sec_vuln_supp_date.strftime("%Y-%m-%d"), "2017-11-30")
        self.assertEqual(p.end_of_support_date.strftime("%Y-%m-%d"), "2025-10-31")

    def test_valid_eox_call_without_create_missing(self):
        test_product = "WS-C3560C-8PC-S"

        sample_record = """{
            "EndOfSvcAttachDate": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2017-06-30"
            },
            "EndOfServiceContractRenewal": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2021-01-28"
            },
            "ProductBulletinNumber": "EOL10691",
            "EOLProductID": "WS-C3560C-8PC-S",
            "LinkToProductBulletinURL": "http://www.cisco.com/c/en/us/products/collateral/switches/catalyst-3560-c-series-switches/eos-eol-notice-c51-736180.html",
            "EOXExternalAnnouncementDate": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2015-10-31"
            },
            "UpdatedTimeStamp": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2015-11-03"
            },
            "EOXMigrationDetails": {
                "MigrationProductInfoURL": "http://www.cisco.com/c/en/us/products/switches/catalyst-3560-cx-series-switches/index.html",
                "PIDActiveFlag": "Y  ",
                "MigrationStrategy": " ",
                "MigrationProductName": " ",
                "MigrationProductId": "WS-C3560CX-8PC-S",
                "MigrationOption": "Enter PID(s)",
                "MigrationInformation": "Cisco Catalyst 3560-CX 8 Port PoE IP Base"
            },
            "EndOfRoutineFailureAnalysisDate": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2017-10-15"
            },
            "EOXInputType": "ShowEOXByPids",
            "EndOfSaleDate": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2016-10-30"
            },
            "EndOfSWMaintenanceReleases": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2017-10-30"
            },
            "EndOfSecurityVulSupportDate": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2017-11-30"
            },
            "EOXInputValue": "WS-C3560C-8PC-S ",
            "LastDateOfSupport": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2025-10-31"
            },
            "ProductIDDescription": "Catalyst 3560C Switch 8 FE PoE, 2 x Dual Uplink, IP Base"
        }"""

        eox_db_json = json.loads(sample_record)
        api_crawler.update_local_db_based_on_record(eox_db_json, create_missing=False)

        # nothing should be in the database
        self.assertEqual(0, Product.objects.all().count())

        # create the test product
        Product.objects.create(product_id=test_product, vendor=Vendor.objects.get(id=1))

        # test that the update timestamp is successful verified
        p = Product.objects.get(product_id=test_product)
        p.eox_update_time_stamp = datetime.now().date()
        p.save()

        # the entry in the database is not touched
        result_record = api_crawler.update_local_db_based_on_record(eox_db_json, create_missing=False)
        self.assertEqual("update suppressed (data not modified)", result_record["message"])
        self.assertFalse(result_record["created"])
        self.assertFalse(result_record["updated"])
        self.assertFalse(result_record["blacklist"])

        # test that the lifecycle data are not touched
        p = Product.objects.get(product_id=test_product)
        self.assertIsNone(p.end_of_sale_date)

        # change update timestamp
        p.eox_update_time_stamp = None
        p.save()

        # update entry in the database
        result_record = api_crawler.update_local_db_based_on_record(eox_db_json, create_missing=False)

        p = Product.objects.get(product_id=test_product)
        self.assertIsNone(result_record["message"])
        self.assertFalse(result_record["created"])
        self.assertTrue(result_record["updated"])
        self.assertFalse(result_record["blacklist"])

        self.assertEqual(p.eox_update_time_stamp.strftime("%Y-%m-%d"), "2015-11-03")
        self.assertEqual(p.end_of_sale_date.strftime("%Y-%m-%d"), "2016-10-30")
        self.assertEqual(p.eol_ext_announcement_date.strftime("%Y-%m-%d"), "2015-10-31")
        self.assertEqual(p.end_of_sw_maintenance_date.strftime("%Y-%m-%d"), "2017-10-30")
        self.assertEqual(p.end_of_routine_failure_analysis.strftime("%Y-%m-%d"), "2017-10-15")
        self.assertEqual(p.end_of_service_contract_renewal.strftime("%Y-%m-%d"), "2021-01-28")
        self.assertEqual(p.end_of_new_service_attachment_date.strftime("%Y-%m-%d"), "2017-06-30")
        self.assertEqual(p.end_of_sec_vuln_supp_date.strftime("%Y-%m-%d"), "2017-11-30")
        self.assertEqual(p.end_of_support_date.strftime("%Y-%m-%d"), "2025-10-31")


@override_settings(APP_CONFIG_FILE="conf/test.TestUpdateCiscoEoXCrawler.config")
class TestUpdateCiscoEoXCrawler(BaseCiscoEoxTestCase):
    fixtures = ["default_vendors.yaml"]
    CONFIG_FILE = "conf/test.TestUpdateCiscoEoXCrawler.config"

    def test_update_with_autocreate(self):
        """
        Test Cisco EoX API update with autocreate products
        """
        test_product = "WS-C3560C-8PC-S"
        self.update_config_file(blacklist="", autocreate=True)

        # execute Cisco API synchronization
        result = update_cisco_eox_database(test_product)

        self.assertEqual(1, Product.objects.all().count())
        self.assertFalse(result[0]["blacklist"])
        self.assertTrue(result[0]["created"])
        self.assertTrue(result[0]["updated"])

        # reset the EoX update timestamp
        p = Product.objects.filter(product_id=test_product).first()
        p.eox_update_time_stamp = None
        p.save()

        # run update again
        result = update_cisco_eox_database(test_product)

        self.assertEqual(1, Product.objects.all().count())
        self.assertFalse(result[0]["blacklist"])
        self.assertFalse(result[0]["created"])
        self.assertTrue(result[0]["updated"])

    def test_update_without_autocreate(self):
        """
        Test Cisco EoX API update without autocreate products
        """
        test_product = "WS-C3560C-8PC-S"
        self.update_config_file(blacklist="", autocreate=False)

        # execute Cisco API synchronization
        result = update_cisco_eox_database(test_product)
        self.assertFalse(result[0]["blacklist"])
        self.assertFalse(result[0]["created"])
        self.assertFalse(result[0]["updated"])

        self.assertEqual(0, Product.objects.all().count())

        # create test product and run again
        Product.objects.create(product_id=test_product)

        # run update again
        result = update_cisco_eox_database(test_product)

        self.assertEqual(1, Product.objects.all().count())
        self.assertFalse(result[0]["blacklist"])
        self.assertFalse(result[0]["created"])
        self.assertTrue(result[0]["updated"])

    def test_update_with_blacklist(self):
        """
        Test Cisco EoX API update with blacklist
        """
        test_product = "WS-C3560C-8PC-S"
        self.update_config_file(blacklist="8PC-S$", autocreate=False)

        # execute Cisco API synchronization
        result = update_cisco_eox_database(test_product)
        self.assertTrue(result[0]["blacklist"])
        self.assertFalse(result[0]["created"])
        self.assertFalse(result[0]["updated"])

        self.assertEqual(0, Product.objects.all().count())


@override_settings(APP_CONFIG_FILE="conf/test.TestCiscoEoxTask.config",
                   CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True)
class TestCiscoEoxTask(BaseCiscoEoxTestCase):
    fixtures = ["default_vendors.yaml"]
    CONFIG_FILE = "conf/test.TestCiscoEoxTask.config"

    def test_cisco_eox_api_sync_task(self):
        """
        test the celery task for the Cisco EoX API synchronization
        """
        test_product = "WS-C3560C-8PC-S"
        self.update_config_file(blacklist="", autocreate=True, queries=test_product)

        _ = execute_task_to_synchronize_cisco_eox_states.delay(ignore_periodic_sync_flag=True)

        # verify the elements in the database
        self.assertEqual(1, Product.objects.all().count())

        p = Product.objects.filter(product_id=test_product).first()
        self.assertIsNotNone(p.end_of_sale_date)
