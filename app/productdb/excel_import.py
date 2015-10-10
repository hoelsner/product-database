import logging
import pandas as pd
from xlrd import XLRDError
from app.productdb.models import Product
from app.productdb.models import Vendor

logger = logging.getLogger(__name__)


class InvalidExcelFileFormat(BaseException):
    """
    Exception thrown if there is an issue with the low level file format
    """
    pass


class InvalidImportFormatException(BaseException):
    """
    Exception thrown if the format of the Excel file for the import is invalid
    """
    pass


class ImportProductsExcelFile:
    workbook = None
    path = None
    valid_file = False
    import_result_messages = []
    valid_imported_products = 0
    invalid_products = 0
    __wb_data_frame__ = None

    def __init__(self, path_to_excel_file=None):
        self.path_to_excel_file = path_to_excel_file

    def __load_workbook__(self):
        try:
            self.workbook = pd.ExcelFile(self.path_to_excel_file)

        except XLRDError as ex:
            logger.error("invalid format of excel file '%s'" % self.path_to_excel_file, ex)
            raise InvalidExcelFileFormat("invalid file format")

        except Exception as ex:
            logger.fatal("unable to read workbook at '%s'" % self.path_to_excel_file, ex)
            raise

    def __create_data_frame__(self):
        self.__wb_data_frame__ = self.workbook.parse('products').dropna(axis=0, subset=['product id'])

    def verify_file(self):
        if self.workbook is None:
            self.__load_workbook__()
        self.valid_file = False

        sheets = self.workbook.sheet_names
        required_sheet = 'products'
        required_keys = {'product id', 'description', 'list price', 'currency', 'vendor'}

        # verify worksheet that is required
        if required_sheet not in sheets:
            raise InvalidImportFormatException("sheet '%s' not found" % required_sheet)

        # verify keys in file
        dframe = self.workbook.parse('products')
        keys = set(dframe.keys())

        if len(required_keys.intersection(keys)) != 5:
            raise InvalidImportFormatException("required keys not found in Excel file")

        self.valid_file = True

    @property
    def amount_of_products(self):
        if self.__wb_data_frame__ is None:
            self.__create_data_frame__()
        return len(self.__wb_data_frame__)

    def is_valid_file(self):
        return self.valid_file

    def import_products_to_database(self):
        if self.workbook is None:
            self.__load_workbook__()
        if self.__wb_data_frame__ is None:
            self.__create_data_frame__()

        self.valid_imported_products = 0
        self.invalid_products = 0
        self.import_result_messages.clear()

        for index, row in self.__wb_data_frame__.iterrows():
            try:
                p, created = Product.objects.get_or_create(product_id=row['product id'])
                if not pd.isnull(row['description']):
                    p.description = row['description']

                if not pd.isnull(row['list price']):
                    p.list_price = row['list price']

                if not pd.isnull(row['currency']):
                    p.currency = row['currency']

                if pd.isnull(row['vendor']):
                    v = Vendor.objects.get(id=0)
                else:
                    v = Vendor.objects.get(name=row['vendor'])
                p.vendor = v

                p.save()

                self.valid_imported_products += 1
                if created:
                    self.import_result_messages.append("created product %s" % p.product_id)
                else:
                    self.import_result_messages.append("update product %s" % p.product_id)

            except Exception as ex:
                msg = "failed product import for %s (%s)" % (row['product id'], ex)
                logger.error(msg, ex)
                self.import_result_messages.append(msg)
                self.invalid_products += 1
