"""
Unit tests for the excel import base classes
"""
from django.test import TestCase
import os
from app.productdb.excel_import import ImportProductsExcelFile, InvalidExcelFileFormat, InvalidImportFormatException
from app.productdb.models import Product, Vendor
import datetime


class TestBaseExcelImport(TestCase):
    fixtures = ['default_vendors.yaml']

    @staticmethod
    def prepare_import_products_excel_file(filename, verify_file=True, start_import=True):
        """
        helping method, that creates a new ImportProductsExcelFile instance based on a "filename" in the test data
        directory
        """
        valid_test_file = os.path.join(os.getcwd(),
                                       "tests",
                                       "data",
                                       filename)

        product_file = ImportProductsExcelFile(valid_test_file)
        if verify_file:
            product_file.verify_file()
        if start_import:
            product_file.import_products_to_database()

        return product_file

    def test_valid_product_import_using_excel_with_currency_column(self):
        """
        test a valid product import using the standard Excel template with separate list price and currency columns
        """
        test_product_ids = [
            'WS-C2960S-48FPD-L',
            'WS-C2960S-48LPD-L',
            'WS-C2960S-24PD-L',
            'WS-C2960S-48TD-L',
            'WS-C2960S-24TD-L',
            'WS-C2960S-48FPS-L',
            'WS-C2960S-48LPS-L',
            'WS-C2960S-24PS-L',
            'CAB-STK-E-0.5M',
            'CAB-STK-E-1M=',
            'CAB-STK-E-1M',
            'CAB-STK-E-3M=',
            'CAB-CONSOLE-RJ45=',
            'CAB-CONSOLE-USB=',
            'EX4200-24F',
            'EX4200-24F-DC',
            'WS-C2960S-48TS-L',
            'WS-C2960S-24TS-L',
            'WS-C2960S-48TS-S',
            'WS-C2960S-24TS-S',
            'C2960S-STACK',
            'C2960S-STACK=',
            'CAB-STK-E-0.5M=',
            'EX4200-24F-S',
            'EX4200-24PX',
        ]
        products = [
            {
                'product id': 'WS-C2960S-48FPD-L',
                'description': 'Catalyst 2960S 48 GigE PoE 740W, 2 x 10G SFP+ LAN Base',
                'list price': 8795,
                'currency': 'USD',
                'vendor': 'Cisco Systems',
            },
            {
                'product id': 'CAB-STK-E-1M',
                'description': 'Cisco FlexStack 1m stacking cable',
                'list price': 100,
                'currency': 'USD',
                'vendor': 'unassigned',
            },
            {
                'product id': 'CAB-STK-E-1M=',
                'description': 'Cisco Bladeswitch 1M stack cable',
                'list price': None,
                'currency': 'USD',
                'vendor': 'Cisco Systems',
            },

        ]
        valid_test_file = os.path.join(os.getcwd(),
                                       "tests",
                                       "data",
                                       "excel_import_products_test.xlsx")

        product_file = ImportProductsExcelFile(valid_test_file)
        product_file.verify_file()

        self.assertTrue(product_file.valid_file, "given excel file has no valid format")

        product_file.import_products_to_database()

        self.assertEqual(product_file.valid_imported_products, 25)
        self.assertEqual(product_file.invalid_products, 0)
        self.assertEqual(product_file.amount_of_products, 25)
        self.assertIsNotNone(product_file.import_result_messages)

        # verify that the expected products are created in the database
        for pid in test_product_ids:
            Product.objects.get(product_id=pid)

        # look at the imported values from the
        for product in products:
            p = Product.objects.get(product_id=product['product id'])
            self.assertEqual(p.description, product['description'])
            self.assertEqual(p.list_price, product['list price'], p.product_id)
            self.assertEqual(p.currency, product['currency'])
            self.assertEqual(p.vendor.name, product['vendor'])

    def test_valid_product_import_in_update_only_mode(self):
        """
        test the import using Excel in update only mode. The file contains 25 entries, but only existing entries
        are updated (we create one entry before starting)
        """
        test_product_ids = [
            'WS-C2960S-48FPD-L'
        ]
        products = [
            {
                'product id': 'WS-C2960S-48FPD-L',
                'description': 'Catalyst 2960S 48 GigE PoE 740W, 2 x 10G SFP+ LAN Base',
                'list price': 8795,
                'currency': 'USD',
                'vendor': 'Cisco Systems',
            }
        ]
        valid_test_file = os.path.join(os.getcwd(),
                                       "tests",
                                       "data",
                                       "excel_import_products_test.xlsx")
        p = Product.objects.create(product_id="WS-C2960S-48FPD-L", vendor=Vendor.objects.get(id=1))

        product_file = ImportProductsExcelFile(valid_test_file)
        product_file.verify_file()

        self.assertTrue(product_file.valid_file, "given excel file has no valid format")

        product_file.import_products_to_database(update_only=True)

        self.assertEqual(product_file.valid_imported_products, 1)
        self.assertEqual(product_file.invalid_products, 0)
        self.assertEqual(product_file.amount_of_products, 25)
        self.assertIsNotNone(product_file.import_result_messages)

        # verify that the expected products are created in the database
        for pid in test_product_ids:
            Product.objects.get(product_id=pid)

        # look at the imported values from the
        for product in products:
            p = Product.objects.get(product_id=product['product id'])
            self.assertEqual(p.description, product['description'])
            self.assertEqual(p.list_price, product['list price'], p.product_id)
            self.assertEqual(p.currency, product['currency'])
            self.assertEqual(p.vendor.name, product['vendor'])

    def test_valid_product_import_using_excel_without_currency_column(self):
        """
        test a valid product import using the standard Excel template with list price
        """
        test_product_ids = [
            'WS-C2960S-48FPD-L',
            'WS-C2960S-48LPD-L',
            'WS-C2960S-24PD-L',
            'WS-C2960S-48TD-L',
            'WS-C2960S-24TD-L',
            'WS-C2960S-48FPS-L',
            'WS-C2960S-48LPS-L',
            'WS-C2960S-24PS-L',
            'CAB-STK-E-0.5M',
            'CAB-STK-E-1M=',
            'CAB-STK-E-1M',
            'CAB-STK-E-3M=',
            'CAB-CONSOLE-RJ45=',
            'CAB-CONSOLE-USB=',
            'EX4200-24F',
            'EX4200-24F-DC',
            'WS-C2960S-48TS-L',
            'WS-C2960S-24TS-L',
            'WS-C2960S-48TS-S',
            'WS-C2960S-24TS-S',
            'C2960S-STACK',
            'C2960S-STACK=',
            'CAB-STK-E-0.5M=',
            'EX4200-24F-S',
            'EX4200-24PX',
        ]
        products = [
            {
                'product id': 'WS-C2960S-48FPD-L',
                'description': 'Catalyst 2960S 48 GigE PoE 740W, 2 x 10G SFP+ LAN Base',
                'list price': 8795,
                'currency': 'USD',
                'vendor': 'Cisco Systems',
            },
            {
                'product id': 'CAB-STK-E-1M',
                'description': 'Cisco FlexStack 1m stacking cable',
                'list price': 100,
                'currency': 'USD',
                'vendor': 'unassigned',
            },
            {
                'product id': 'CAB-STK-E-1M=',
                'description': 'Cisco Bladeswitch 1M stack cable',
                'list price': None,
                'currency': 'USD',
                'vendor': 'Cisco Systems',
            },

        ]
        valid_test_file = os.path.join(os.getcwd(),
                                       "tests",
                                       "data",
                                       "excel_import_products_test-wo_currency.xlsx")

        product_file = ImportProductsExcelFile(valid_test_file)
        product_file.verify_file()

        self.assertTrue(product_file.valid_file, "given excel file has no valid format")

        product_file.import_products_to_database()

        self.assertEqual(product_file.valid_imported_products, 25, "\n".join([l for l in product_file.import_result_messages]))
        self.assertEqual(product_file.invalid_products, 0)
        self.assertEqual(product_file.amount_of_products, 25)
        self.assertIsNotNone(product_file.import_result_messages)

        # verify that the expected products are created in the database
        for pid in test_product_ids:
            Product.objects.get(product_id=pid)

        # look at the imported values from the
        for product in products:
            p = Product.objects.get(product_id=product['product id'])
            self.assertEqual(p.description, product['description'])
            self.assertEqual(p.list_price, product['list price'])
            self.assertEqual(p.currency, product['currency'])
            self.assertEqual(p.vendor.name, product['vendor'])

    def test_valid_product_import_with_eox_update_timestamp_date_using_excel_file(self):
        lc_product_id = "WS-C2960S-48FPD-L"
        no_lc_product_id = "EX4200-24PX"
        _ = self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        self.assertIsNotNone(lc_product.eox_update_time_stamp)
        self.assertIsNone(no_lc_product.eox_update_time_stamp)
        self.assertEqual(datetime.date(2016, 1, 1), lc_product.eox_update_time_stamp)

    def test_valid_product_import_with_eol_announcement_date_using_excel_file(self):
        lc_product_id = "WS-C2960S-48LPD-L"
        no_lc_product_id = "EX4200-24PX"
        _ = self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        self.assertIsNotNone(lc_product.eol_ext_announcement_date)
        self.assertIsNone(no_lc_product.eol_ext_announcement_date)
        self.assertEqual(datetime.date(2016, 1, 1), lc_product.eol_ext_announcement_date)

    def test_valid_product_import_with_eos_date_using_excel_file(self):
        lc_product_id = "WS-C2960S-24PD-L"
        no_lc_product_id = "EX4200-24PX"
        _ = self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        self.assertIsNotNone(lc_product.end_of_sale_date)
        self.assertIsNone(no_lc_product.end_of_sale_date)
        self.assertEqual(datetime.date(2016, 1, 1), lc_product.end_of_sale_date)

    def test_valid_product_import_with_end_of_new_service_attachment_date_using_excel_file(self):
        lc_product_id = "WS-C2960S-48TD-L"
        no_lc_product_id = "EX4200-24PX"
        _ = self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        self.assertIsNone(lc_product.end_of_sale_date)
        self.assertIsNotNone(lc_product.end_of_new_service_attachment_date)
        self.assertIsNone(no_lc_product.end_of_new_service_attachment_date)
        self.assertEqual(datetime.date(2016, 1, 1), lc_product.end_of_new_service_attachment_date)

    def test_valid_product_import_with_end_of_sw_maintenance_date_using_excel_file(self):
        lc_product_id = "WS-C2960S-24TD-L"
        no_lc_product_id = "EX4200-24PX"
        _ = self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        self.assertIsNone(lc_product.end_of_sale_date)
        self.assertIsNotNone(lc_product.end_of_sw_maintenance_date)
        self.assertIsNone(no_lc_product.end_of_sw_maintenance_date)
        self.assertEqual(datetime.date(2016, 1, 1), lc_product.end_of_sw_maintenance_date)

    def test_valid_product_import_with_end_of_routine_failure_analysis_using_excel_file(self):
        lc_product_id = "WS-C2960S-48FPS-L"
        no_lc_product_id = "EX4200-24PX"
        _ = self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        self.assertIsNone(lc_product.end_of_sale_date)
        self.assertIsNotNone(lc_product.end_of_routine_failure_analysis)
        self.assertIsNone(no_lc_product.end_of_routine_failure_analysis)
        self.assertEqual(datetime.date(2016, 1, 1), lc_product.end_of_routine_failure_analysis)

    def test_valid_product_import_with_end_of_service_contract_renewal_using_excel_file(self):
        lc_product_id = "WS-C2960S-48LPS-L"
        no_lc_product_id = "EX4200-24PX"
        _ = self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        self.assertIsNone(lc_product.end_of_sale_date)
        self.assertIsNotNone(lc_product.end_of_service_contract_renewal)
        self.assertIsNone(no_lc_product.end_of_service_contract_renewal)
        self.assertEqual(datetime.date(2016, 1, 1), lc_product.end_of_service_contract_renewal)

    def test_valid_product_import_with_end_of_support_date_using_excel_file(self):
        lc_product_id = "WS-C2960S-24PS-L"
        no_lc_product_id = "EX4200-24PX"
        _ = self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        self.assertIsNone(lc_product.end_of_sale_date)
        self.assertIsNotNone(lc_product.end_of_support_date)
        self.assertIsNone(no_lc_product.end_of_support_date)
        self.assertEqual(datetime.date(2016, 1, 1), lc_product.end_of_support_date)

    def test_valid_product_import_with_end_of_sec_vuln_supp_date_using_excel_file(self):
        lc_product_id = "CAB-STK-E-0.5M"
        no_lc_product_id = "EX4200-24PX"
        _ = self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        self.assertIsNone(lc_product.end_of_sale_date)
        self.assertIsNotNone(lc_product.end_of_sec_vuln_supp_date)
        self.assertIsNone(no_lc_product.end_of_sec_vuln_supp_date)
        self.assertEqual(datetime.date(2016, 1, 1), lc_product.end_of_sec_vuln_supp_date)

    def test_valid_product_import_with_eol_note_using_excel_file(self):
        lc_product_id = "CAB-STK-E-1M="
        no_lc_product_id = "EX4200-24PX"
        _ = self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        self.assertIsNone(lc_product.end_of_sale_date)
        self.assertIsNotNone(lc_product.eol_reference_url)
        self.assertIsNotNone(lc_product.eol_reference_number)
        self.assertIsNone(no_lc_product.eol_reference_url)
        self.assertEqual("http://localhost/myurl", lc_product.eol_reference_url)
        self.assertEqual("My Friendly Name", lc_product.eol_reference_number)

        # test without eol_reference_number
        lc_product_id = "CAB-STK-E-1M"
        lc_product = Product.objects.get(product_id=lc_product_id)

        self.assertIsNotNone(lc_product.eol_reference_url)
        self.assertIsNone(lc_product.eol_reference_number)
        self.assertEqual("http://localhost/myurl", lc_product.eol_reference_url)

    def test_valid_product_import_with_full_lifecycle_data_using_excel_file(self):
        lc_product_id = "CAB-STK-E-3M="
        _ = self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)

        self.assertEqual(datetime.date(2016, 1, 1), lc_product.eox_update_time_stamp)
        self.assertEqual(datetime.date(2016, 1, 2), lc_product.eol_ext_announcement_date)
        self.assertEqual(datetime.date(2016, 1, 3), lc_product.end_of_sale_date)
        self.assertEqual(datetime.date(2016, 1, 4), lc_product.end_of_new_service_attachment_date)
        self.assertEqual(datetime.date(2016, 1, 5), lc_product.end_of_sw_maintenance_date)
        self.assertEqual(datetime.date(2016, 1, 6), lc_product.end_of_routine_failure_analysis)
        self.assertEqual(datetime.date(2016, 1, 7), lc_product.end_of_service_contract_renewal)
        self.assertEqual(datetime.date(2016, 1, 8), lc_product.end_of_sec_vuln_supp_date)
        self.assertEqual(datetime.date(2016, 1, 9), lc_product.end_of_support_date)
        self.assertEqual("http://localhost", lc_product.eol_reference_url)
        self.assertEqual("comment", lc_product.eol_reference_number)

    def test_change_product_list_price_by_excel_upload_with_separate_currency_column(self):
        lc_product_id = "WS-C2960S-48FPD-L"
        lc_product = Product.objects.create(product_id=lc_product_id)
        lc_product.list_price = 1.0
        lc_product.save()

        _ = self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)

        self.assertEqual(8795.0, lc_product.list_price)

    def test_change_product_list_price_by_excel_upload_without_separate_currency_column(self):
        lc_product_id = "WS-C2960S-48FPD-L"
        lc_product = Product.objects.create(product_id=lc_product_id)
        lc_product.list_price = 1.0
        lc_product.save()

        _ = self.prepare_import_products_excel_file("excel_import_products_test-wo_currency.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)

        self.assertEqual(8795.0, lc_product.list_price)

    def test_invalid_product_import_using_excel_file_with_invalid_keys(self):
        valid_test_file = os.path.join(os.getcwd(),
                                       "tests",
                                       "data",
                                       "excel_import_products_test-invalid_keys.xlsx")

        product_file = ImportProductsExcelFile(valid_test_file)

        with self.assertRaises(InvalidImportFormatException):
            product_file.verify_file()

    def test_invalid_product_import_using_excel_file_with_invalid_table_name(self):
        valid_test_file = os.path.join(os.getcwd(),
                                       "tests",
                                       "data",
                                       "excel_import_products_test-invalid_table_name.xlsx")

        product_file = ImportProductsExcelFile(valid_test_file)

        with self.assertRaises(InvalidImportFormatException):
            product_file.verify_file()

    def test_invalid_product_import_using_invalid_file(self):
        valid_test_file = os.path.join(os.getcwd(),
                                       "tests",
                                       "data",
                                       "create_cisco_test_data.json")

        product_file = ImportProductsExcelFile(valid_test_file)

        with self.assertRaises(InvalidExcelFileFormat):
            product_file.verify_file()
