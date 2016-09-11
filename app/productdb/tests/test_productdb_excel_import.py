"""
Test suite for the productdb.excel_import module
"""
import os
import pandas as pd
import pytest
import datetime
from reversion.models import Version
from django.contrib.auth.models import User
from mixer.backend.django import mixer
from app.productdb.excel_import import ImportProductsExcelFile, InvalidImportFormatException, InvalidExcelFileFormat
from app.productdb.models import Product, Vendor, ProductGroup

pytestmark = pytest.mark.django_db

TEST_DATA_COLUMNS = [
    "product id",
    "description",
    "list price",
    "currency",
    "vendor",
    "eox update timestamp",
    "eol announcement date",
    "end of sale date",
    "end of new service attachment date",
    "end of sw maintenance date",
    "end of routing failure analysis date",
    "end of service contract renewal date",
    "last date of support",
    "end of security/vulnerability support date",
]
DEFAULT_TEST_DATA_FRAME = pd.DataFrame(
    [
        [
            "Product A",
            "description of Product A",
            "4000.00",
            "USD",
            "Cisco Systems",
            datetime.datetime(2016, 1, 1),
            datetime.datetime(2016, 1, 2),
            datetime.datetime(2016, 1, 3),
            datetime.datetime(2016, 1, 4),
            datetime.datetime(2016, 1, 5),
            datetime.datetime(2016, 1, 6),
            datetime.datetime(2016, 1, 7),
            datetime.datetime(2016, 1, 8),
            datetime.datetime(2016, 1, 9),
        ],
        [
            "Product B",
            "description of Product B",
            "6000.00",
            "USD",
            "Cisco Systems",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ]
    ], columns=TEST_DATA_COLUMNS
)
CURRENT_TEST_DATA = DEFAULT_TEST_DATA_FRAME.copy()


class BaseImportProductsExcelFileMock(ImportProductsExcelFile):
    def verify_file(self):
        # set validation to true unconditional
        self.valid_file = True

    def __load_workbook__(self):
        # ignore the load workbook function
        return

    def __create_data_frame__(self):
        # add a predefined DataFrame for the file import
        self.__wb_data_frame__ = CURRENT_TEST_DATA


@pytest.fixture
def apply_base_import_products_excel_file_mock(monkeypatch):
    monkeypatch.setattr("test_productdb_excel_import.ImportProductsExcelFile", BaseImportProductsExcelFileMock)


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
class TestImportProductsExcelFile:
    @pytest.mark.usefixtures("apply_base_import_products_excel_file_mock")
    def test_valid_import(self):
        product_file = ImportProductsExcelFile("virtual_file.xlsx")
        assert product_file.is_valid_file() is False

        product_file.verify_file()
        assert product_file.is_valid_file() is True

        product_file.import_products_to_database()
        assert product_file.amount_of_products == 2
        assert Product.objects.count() == 2

        p = Product.objects.get(product_id="Product A")
        assert p.description == "description of Product A"
        assert p.list_price == 4000.0
        assert p.currency == "USD"
        assert p.vendor == Vendor.objects.get(id=1)
        assert p.eox_update_time_stamp == datetime.date(2016, 1, 1)
        assert p.eol_ext_announcement_date == datetime.date(2016, 1, 2)
        assert p.end_of_sale_date == datetime.date(2016, 1, 3)
        assert p.end_of_new_service_attachment_date == datetime.date(2016, 1, 4)
        assert p.end_of_sw_maintenance_date == datetime.date(2016, 1, 5)
        assert p.end_of_routine_failure_analysis == datetime.date(2016, 1, 6)
        assert p.end_of_service_contract_renewal == datetime.date(2016, 1, 7)
        assert p.end_of_support_date == datetime.date(2016, 1, 8)
        assert p.end_of_sec_vuln_supp_date == datetime.date(2016, 1, 9)

        p = Product.objects.get(product_id="Product B")
        assert p.description == "description of Product B"
        assert p.list_price == 6000.0
        assert p.currency == "USD"
        assert p.vendor == Vendor.objects.get(id=1)
        assert p.eox_update_time_stamp is None
        assert p.eol_ext_announcement_date is None
        assert p.end_of_sale_date is None
        assert p.end_of_new_service_attachment_date is None
        assert p.end_of_sw_maintenance_date is None
        assert p.end_of_routine_failure_analysis is None
        assert p.end_of_service_contract_renewal is None
        assert p.end_of_support_date is None
        assert p.end_of_sec_vuln_supp_date is None

    @pytest.mark.usefixtures("apply_base_import_products_excel_file_mock")
    def test_import_with_list_price_of_zero(self):
        """Should ensure that a list price of 0 is saved as 0 value, not None/Null value"""
        global CURRENT_TEST_DATA
        CURRENT_TEST_DATA = pd.DataFrame(
            [
                [
                    "Product A",
                    "description of Product A",
                    "0",
                    "USD",
                    "Cisco Systems",
                    datetime.datetime(2016, 1, 1),
                    datetime.datetime(2016, 1, 2),
                    datetime.datetime(2016, 1, 3),
                    datetime.datetime(2016, 1, 4),
                    datetime.datetime(2016, 1, 5),
                    datetime.datetime(2016, 1, 6),
                    datetime.datetime(2016, 1, 7),
                    datetime.datetime(2016, 1, 8),
                    datetime.datetime(2016, 1, 9),
                ],
                [
                    "Product B",
                    "description of Product B",
                    "0.00",
                    "USD",
                    "Cisco Systems",
                    datetime.datetime(2016, 1, 1),
                    datetime.datetime(2016, 1, 2),
                    datetime.datetime(2016, 1, 3),
                    datetime.datetime(2016, 1, 4),
                    datetime.datetime(2016, 1, 5),
                    datetime.datetime(2016, 1, 6),
                    datetime.datetime(2016, 1, 7),
                    datetime.datetime(2016, 1, 8),
                    datetime.datetime(2016, 1, 9),
                ],
                [
                    "Product A2",
                    "description of Product A",
                    0,
                    "USD",
                    "Cisco Systems",
                    datetime.datetime(2016, 1, 1),
                    datetime.datetime(2016, 1, 2),
                    datetime.datetime(2016, 1, 3),
                    datetime.datetime(2016, 1, 4),
                    datetime.datetime(2016, 1, 5),
                    datetime.datetime(2016, 1, 6),
                    datetime.datetime(2016, 1, 7),
                    datetime.datetime(2016, 1, 8),
                    datetime.datetime(2016, 1, 9),
                ],
                [
                    "Product B2",
                    "description of Product B",
                    0.00,
                    "USD",
                    "Cisco Systems",
                    datetime.datetime(2016, 1, 1),
                    datetime.datetime(2016, 1, 2),
                    datetime.datetime(2016, 1, 3),
                    datetime.datetime(2016, 1, 4),
                    datetime.datetime(2016, 1, 5),
                    datetime.datetime(2016, 1, 6),
                    datetime.datetime(2016, 1, 7),
                    datetime.datetime(2016, 1, 8),
                    datetime.datetime(2016, 1, 9),
                ],
                [
                    "Product C",
                    "description of Product C",
                    "",
                    "USD",
                    "Cisco Systems",
                    datetime.datetime(2016, 1, 1),
                    datetime.datetime(2016, 1, 2),
                    datetime.datetime(2016, 1, 3),
                    datetime.datetime(2016, 1, 4),
                    datetime.datetime(2016, 1, 5),
                    datetime.datetime(2016, 1, 6),
                    datetime.datetime(2016, 1, 7),
                    datetime.datetime(2016, 1, 8),
                    datetime.datetime(2016, 1, 9),
                ]
            ], columns=TEST_DATA_COLUMNS
        )
        user = User.objects.get(username="api")
        product_file = ImportProductsExcelFile(
            "virtual_file.xlsx",
            user_for_revision=user
        )
        product_file.verify_file()
        product_file.import_products_to_database()
        assert Product.objects.count() == 5

        # verify imported data
        pa = Product.objects.get(product_id="Product A")
        assert pa.list_price is not None
        assert pa.list_price == 0.00

        pa2 = Product.objects.get(product_id="Product A2")
        assert pa2.list_price is not None
        assert pa2.list_price == 0.00

        pb = Product.objects.get(product_id="Product B")
        assert pb.list_price is not None
        assert pb.list_price == 0.00

        pb2 = Product.objects.get(product_id="Product B2")
        assert pb2.list_price is not None
        assert pb2.list_price == 0.00

        pc = Product.objects.get(product_id="Product C")
        assert pc.list_price is None, "No list price provided, therefore it should be None"

    @pytest.mark.usefixtures("apply_base_import_products_excel_file_mock")
    def test_valid_import_with_revision_user(self):
        global CURRENT_TEST_DATA
        CURRENT_TEST_DATA = DEFAULT_TEST_DATA_FRAME

        user = User.objects.get(username="api")
        product_file = ImportProductsExcelFile(
            "virtual_file.xlsx",
            user_for_revision=user
        )
        product_file.verify_file()
        product_file.import_products_to_database()
        assert Product.objects.count() == 2

        # verify reversion comment
        versions = Version.objects.all()
        assert len(versions) == 2, "Should be two reversion"
        assert "manual product import" == versions.first().revision.comment
        assert user == versions.first().revision.user

    def test_invalid_file(self):
        valid_test_file = os.path.join(os.getcwd(), "tests", "data", "file_not_found.xlsx")
        product_file = ImportProductsExcelFile(valid_test_file)

        with pytest.raises(Exception) as exinfo:
            product_file.verify_file()

        assert exinfo.match("No such file or directory:")


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
class TestMigratedImportProductsExcelFile:
    """test cases before pytest"""

    @staticmethod
    def prepare_import_products_excel_file(filename, verify_file=True, start_import=True):
        valid_test_file = os.path.join(os.getcwd(), "tests", "data", filename)

        product_file = ImportProductsExcelFile(valid_test_file)
        if verify_file:
            product_file.verify_file()
            if start_import:
                product_file.import_products_to_database()

        return product_file

    def test_valid_product_import_using_excel_with_currency_column(self):
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
            }
        ]
        product_file = self.prepare_import_products_excel_file("excel_import_products_test.xlsx")

        assert product_file.valid_imported_products == 25
        assert product_file.invalid_products == 0
        assert product_file.amount_of_products == 25
        assert product_file.import_result_messages is not None

        # verify that the expected products are created in the database
        for pid in test_product_ids:
            Product.objects.get(product_id=pid)

        # look at the imported values from the
        for product in products:
            p = Product.objects.get(product_id=product['product id'])
            assert p.description == product['description']
            assert p.list_price == product['list price']
            assert p.currency == product['currency']
            assert p.vendor.name == product['vendor']

    def test_valid_product_import_in_update_only_mode(self):
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
        mixer.blend("productdb.Product", product_id="WS-C2960S-48FPD-L", vendor=Vendor.objects.get(id=1))

        product_file = self.prepare_import_products_excel_file("excel_import_products_test.xlsx", start_import=False)
        product_file.import_products_to_database(update_only=True)

        assert product_file.valid_imported_products == 1
        assert product_file.invalid_products == 0
        assert product_file.amount_of_products == 25
        assert product_file.import_result_messages is not None

        # verify that the expected products are created in the database
        for pid in test_product_ids:
            Product.objects.get(product_id=pid)

        # look at the imported values from the
        for product in products:
            p = Product.objects.get(product_id=product['product id'])
            assert p.description == product['description']
            assert p.list_price == product['list price']
            assert p.currency == product['currency']
            assert p.vendor.name == product['vendor']

    def test_valid_product_import_using_excel_without_currency_column(self):
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
            }
        ]
        product_file = self.prepare_import_products_excel_file("excel_import_products_test-wo_currency.xlsx")

        assert product_file.valid_imported_products == 25, "\n".join([l for l in product_file.import_result_messages])
        assert product_file.invalid_products == 0
        assert product_file.amount_of_products == 25
        assert product_file.import_result_messages is not None

        # verify that the expected products are created in the database
        for pid in test_product_ids:
            Product.objects.get(product_id=pid)

        # look at the imported values from the
        for product in products:
            p = Product.objects.get(product_id=product['product id'])
            assert p.description == product['description']
            assert p.list_price == product['list price']
            assert p.currency == product['currency']
            assert p.vendor.name == product['vendor']

    def test_valid_product_import_with_eox_update_timestamp_date_using_excel_file(self):
        lc_product_id = "WS-C2960S-48FPD-L"
        no_lc_product_id = "EX4200-24PX"
        self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        assert lc_product.eox_update_time_stamp is not None
        assert no_lc_product.eox_update_time_stamp is None
        assert datetime.date(2016, 1, 1) == lc_product.eox_update_time_stamp

    def test_valid_product_import_with_eol_announcement_date_using_excel_file(self):
        lc_product_id = "WS-C2960S-48LPD-L"
        no_lc_product_id = "EX4200-24PX"
        self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        assert lc_product.eol_ext_announcement_date is not None
        assert no_lc_product.eol_ext_announcement_date is None
        assert datetime.date(2016, 1, 1) == lc_product.eol_ext_announcement_date

    def test_valid_product_import_with_eos_date_using_excel_file(self):
        lc_product_id = "WS-C2960S-24PD-L"
        no_lc_product_id = "EX4200-24PX"
        self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        assert lc_product.end_of_sale_date is not None
        assert no_lc_product.end_of_sale_date is None
        assert datetime.date(2016, 1, 1) == lc_product.end_of_sale_date

    def test_valid_product_import_with_end_of_new_service_attachment_date_using_excel_file(self):
        lc_product_id = "WS-C2960S-48TD-L"
        no_lc_product_id = "EX4200-24PX"
        self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        assert lc_product.end_of_sale_date is None
        assert lc_product.end_of_new_service_attachment_date is not None
        assert no_lc_product.end_of_new_service_attachment_date is None
        assert datetime.date(2016, 1, 1) == lc_product.end_of_new_service_attachment_date

    def test_valid_product_import_with_end_of_sw_maintenance_date_using_excel_file(self):
        lc_product_id = "WS-C2960S-24TD-L"
        no_lc_product_id = "EX4200-24PX"
        self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        assert lc_product.end_of_sale_date is None
        assert lc_product.end_of_sw_maintenance_date is not None
        assert no_lc_product.end_of_sw_maintenance_date is None
        assert datetime.date(2016, 1, 1) == lc_product.end_of_sw_maintenance_date

    def test_valid_product_import_with_end_of_routine_failure_analysis_using_excel_file(self):
        lc_product_id = "WS-C2960S-48FPS-L"
        no_lc_product_id = "EX4200-24PX"
        self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        assert lc_product.end_of_sale_date is None
        assert lc_product.end_of_routine_failure_analysis is not None
        assert no_lc_product.end_of_routine_failure_analysis is None
        assert datetime.date(2016, 1, 1) == lc_product.end_of_routine_failure_analysis

    def test_valid_product_import_with_end_of_service_contract_renewal_using_excel_file(self):
        lc_product_id = "WS-C2960S-48LPS-L"
        no_lc_product_id = "EX4200-24PX"
        self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        assert lc_product.end_of_sale_date is None
        assert lc_product.end_of_service_contract_renewal is not None
        assert no_lc_product.end_of_service_contract_renewal is None
        assert datetime.date(2016, 1, 1) == lc_product.end_of_service_contract_renewal

    def test_valid_product_import_with_end_of_support_date_using_excel_file(self):
        lc_product_id = "WS-C2960S-24PS-L"
        no_lc_product_id = "EX4200-24PX"
        self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        assert lc_product.end_of_sale_date is None
        assert lc_product.end_of_support_date is not None
        assert no_lc_product.end_of_support_date is None
        assert datetime.date(2016, 1, 1), lc_product.end_of_support_date

    def test_valid_product_import_with_end_of_sec_vuln_supp_date_using_excel_file(self):
        lc_product_id = "CAB-STK-E-0.5M"
        no_lc_product_id = "EX4200-24PX"
        self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        assert lc_product.end_of_sale_date is None
        assert lc_product.end_of_sec_vuln_supp_date is not None
        assert no_lc_product.end_of_sec_vuln_supp_date is None
        assert datetime.date(2016, 1, 1) == lc_product.end_of_sec_vuln_supp_date

    def test_valid_product_import_with_eol_note_using_excel_file(self):
        lc_product_id = "CAB-STK-E-1M="
        no_lc_product_id = "EX4200-24PX"
        self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)
        no_lc_product = Product.objects.get(product_id=no_lc_product_id)

        assert lc_product.end_of_sale_date is None
        assert lc_product.eol_reference_url is not None
        assert lc_product.eol_reference_number is not None
        assert no_lc_product.eol_reference_url is None
        assert "http://localhost/myurl" == lc_product.eol_reference_url
        assert "My Friendly Name" == lc_product.eol_reference_number

        # test without eol_reference_number
        lc_product_id = "CAB-STK-E-1M"
        lc_product = Product.objects.get(product_id=lc_product_id)

        assert lc_product.eol_reference_url is not None
        assert lc_product.eol_reference_number is None
        assert "http://localhost/myurl" == lc_product.eol_reference_url

    def test_valid_product_import_with_full_lifecycle_data_using_excel_file(self):
        lc_product_id = "CAB-STK-E-3M="
        self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)

        assert datetime.date(2016, 1, 1) == lc_product.eox_update_time_stamp
        assert datetime.date(2016, 1, 2) == lc_product.eol_ext_announcement_date
        assert datetime.date(2016, 1, 3) == lc_product.end_of_sale_date
        assert datetime.date(2016, 1, 4) == lc_product.end_of_new_service_attachment_date
        assert datetime.date(2016, 1, 5) == lc_product.end_of_sw_maintenance_date
        assert datetime.date(2016, 1, 6) == lc_product.end_of_routine_failure_analysis
        assert datetime.date(2016, 1, 7) == lc_product.end_of_service_contract_renewal
        assert datetime.date(2016, 1, 8) == lc_product.end_of_sec_vuln_supp_date
        assert datetime.date(2016, 1, 9) == lc_product.end_of_support_date
        assert "http://localhost" == lc_product.eol_reference_url
        assert "comment" == lc_product.eol_reference_number

    def test_ignore_list_price_by_excel_upload_with_separate_currency_column(self):
        lc_product_id = "WS-C2960S-48FPD-L"
        lc_product = Product.objects.create(product_id=lc_product_id)
        lc_product.list_price = 1.0
        lc_product.currency = "EUR"
        lc_product.save()

        self.prepare_import_products_excel_file("excel_import_products_test-without_list_prices.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)

        assert 1.0 == lc_product.list_price
        assert "EUR" == lc_product.currency

    def test_change_product_list_price_by_excel_upload_with_separate_currency_column(self):
        lc_product_id = "WS-C2960S-48FPD-L"
        lc_product = Product.objects.create(product_id=lc_product_id)
        lc_product.list_price = 1.0
        lc_product.save()

        self.prepare_import_products_excel_file("excel_import_products_test-with_eol_data.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)

        assert 8795.0 == lc_product.list_price

    def test_change_product_list_price_by_excel_upload_without_separate_currency_column(self):
        lc_product_id = "WS-C2960S-48FPD-L"
        lc_product = Product.objects.create(product_id=lc_product_id)
        lc_product.list_price = 1.0
        lc_product.save()

        self.prepare_import_products_excel_file("excel_import_products_test-wo_currency.xlsx")

        # verify the lifecycle information for the test products
        lc_product = Product.objects.get(product_id=lc_product_id)

        assert 8795.0 == lc_product.list_price

    def test_invalid_product_import_using_excel_file_with_invalid_keys(self):
        product_file = self.prepare_import_products_excel_file(
            "excel_import_products_test-invalid_keys.xlsx",
            verify_file=False
        )

        with pytest.raises(InvalidImportFormatException):
            product_file.verify_file()

    def test_invalid_product_import_using_excel_file_with_invalid_table_name(self):
        product_file = self.prepare_import_products_excel_file(
            "excel_import_products_test-invalid_table_name.xlsx",
            verify_file=False
        )

        with pytest.raises(InvalidImportFormatException):
            product_file.verify_file()

    def test_invalid_product_import_using_invalid_file(self):
        product_file = self.prepare_import_products_excel_file(
            "cisco_test_data.json",
            verify_file=False
        )

        with pytest.raises(InvalidExcelFileFormat):
            product_file.verify_file()

    def test_import_with_product_group(self):
        my_first_group_name = "My First Group"
        my_first_group_list = [
            "WS-C2960S-48FPD-L",
            "WS-C2960S-24PD-L",
            "WS-C2960S-24TD-L",
        ]
        my_second_group_name = "My Second Group"
        my_second_group_list = [
            "WS-C2960S-48LPD-L",
            "WS-C2960S-48TD-L",
            "WS-C2960S-48FPS-L",
        ]
        example_none_value = "WS-C2960S-48LPS-L"
        cis_vendor = Vendor.objects.get(id=1)
        assert ProductGroup.objects.all().count() == 0

        self.prepare_import_products_excel_file("excel_import_products_test-with_product_group.xlsx")
        assert ProductGroup.objects.all().count() == 2

        # get new objects
        pg1 = ProductGroup.objects.filter(name=my_first_group_name).first()
        pg2 = ProductGroup.objects.filter(name=my_second_group_name).first()
        assert pg1.vendor == cis_vendor
        assert pg2.vendor == cis_vendor

        # verify products in list
        assert len(my_first_group_list) == pg1.get_all_products().count()
        result_first_elements = sorted([e.product_id for e in pg1.get_all_products()])
        my_first_group_list.sort()
        assert result_first_elements == my_first_group_list

        assert len(my_second_group_list) == pg2.get_all_products().count()
        result_second_elements = sorted([e.product_id for e in pg2.get_all_products()])
        my_second_group_list.sort()
        assert result_second_elements == my_second_group_list

        # test that given value has no group assignment
        p = Product.objects.get(product_id=example_none_value)
        assert p.product_group is None
