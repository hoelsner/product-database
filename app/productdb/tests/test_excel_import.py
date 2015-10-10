"""
Unit tests for the excel import base classes
"""
from django.test import TestCase
import os
from app.productdb.excel_import import ImportProductsExcelFile, InvalidExcelFileFormat, InvalidImportFormatException
from app.productdb.models import Product


class TestBaseExcelImport(TestCase):
    fixtures = ['default_vendors.yaml']

    def test_valid_product_import_using_excel_file(self):
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
            self.assertEqual(p.list_price, product['list price'])
            self.assertEqual(p.currency, product['currency'])
            self.assertEqual(p.vendor.name, product['vendor'])

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
