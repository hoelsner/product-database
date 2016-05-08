from django.test import TestCase
from app.productdb.crawler import cisco_eox_api_crawler
from app.productdb.models import Settings, Product
import json
import os


class TestCiscoEoxCrawler(TestCase):
    """
    test the Cisco EoX API classes
    """
    fixtures = ['default_vendors.yaml']

    def test_eox_update_call_with_sample_data(self):
        s, create = Settings.objects.get_or_create(id=1)
        s.cisco_api_enabled = True
        s.cisco_eox_api_auto_sync_enabled = True
        eox_sample_response = os.path.join("app",
                                           "productdb",
                                           "tests",
                                           "test_crawler",
                                           "cisco_eox_sample_response.json")
        eox_db_json = json.loads(open(eox_sample_response).read())

        for record in eox_db_json['EOXRecord']:
            cisco_eox_api_crawler.update_local_db_based_on_record(record, True)

    def test_eox_update_call_with_special_character(self):
        """
        test, that no issue exists when the '%' sign is present in the ProductID
        :return:
        """
        s, create = Settings.objects.get_or_create(id=1)
        s.cisco_api_enabled = True
        s.cisco_eox_api_auto_sync_enabled = True
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
        cisco_eox_api_crawler.update_local_db_based_on_record(eox_db_json, True)

        p = Product.objects.get(product_id="SPARE%")

    def test_valid_eox_call_with_validated_date_format(self):
        test_product = "WS-C3560C-8PC-S"

        sample_record = """{
            "EndOfSvcAttachDate": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2017-10-30"
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
                "value": "2017-10-30"
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
            "EOXInputValue": "WS-C3560C-8PC-S ",
            "LastDateOfSupport": {
                "dateFormat": "YYYY-MM-DD",
                "value": "2021-10-31"
            },
            "ProductIDDescription": "Catalyst 3560C Switch 8 FE PoE, 2 x Dual Uplink, IP Base"
        }"""

        eox_db_json = json.loads(sample_record)
        cisco_eox_api_crawler.update_local_db_based_on_record(eox_db_json, True)

        p = Product.objects.get(product_id=test_product)

        self.assertEqual(p.end_of_support_date.strftime("%Y-%m-%d"), "2021-10-31")
