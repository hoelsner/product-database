import logging
import pandas as pd
from django.db import transaction
from reversion import revisions as reversion
from xlrd import XLRDError
from app.productdb.models import Product
from app.productdb.models import Vendor

logger = logging.getLogger(__name__)


class InvalidExcelFileFormat(Exception):
    """
    Exception thrown if there is an issue with the low level file format
    """
    pass


class InvalidImportFormatException(Exception):
    """
    Exception thrown if the format of the Excel file for the import is invalid
    """
    pass


class ImportProductsExcelFile:
    workbook = None
    path = None
    valid_file = False
    user_for_revision = None
    import_result_messages = []
    valid_imported_products = 0
    invalid_products = 0
    __wb_data_frame__ = None

    def __init__(self, path_to_excel_file=None, user_for_revision=None):
        self.path_to_excel_file = path_to_excel_file
        if user_for_revision:
            self.user_for_revision = user_for_revision

    def __load_workbook__(self):
        try:
            self.workbook = pd.ExcelFile(self.path_to_excel_file)

        except XLRDError as ex:
            logger.error("invalid format of excel file '%s' (%s)" % (self.path_to_excel_file, ex))
            raise InvalidExcelFileFormat("invalid file format") from ex

        except Exception:
            logger.fatal("unable to read workbook at '%s'" % self.path_to_excel_file)
            raise

    def __create_data_frame__(self):
        self.__wb_data_frame__ = self.workbook.parse(
            "products", converters={
                "product id": str,
                "description": str,
                "list price": str,
                "currency": str,
                "vendor": str
            }
        ).dropna(axis=0, subset=["product id"])

    def verify_file(self):
        if self.workbook is None:
            self.__load_workbook__()
        self.valid_file = False

        sheets = self.workbook.sheet_names
        required_sheet = "products"
        required_keys = {"product id", "description", "list price", "currency", "vendor"}

        # verify worksheet that is required
        if required_sheet not in sheets:
            raise InvalidImportFormatException("sheet '%s' not found" % required_sheet)

        # verify keys in file
        dframe = self.workbook.parse("products")
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

    def import_products_to_database(self, status_callback=None):
        """
        Import products from the associated excel sheet to the database
        """
        if self.workbook is None:
            self.__load_workbook__()
        if self.__wb_data_frame__ is None:
            self.__create_data_frame__()

        self.valid_imported_products = 0
        self.invalid_products = 0
        self.import_result_messages.clear()
        amount_of_entries = len(self.__wb_data_frame__.index)

        # process entries in file
        current_entry = 1
        for index, row in self.__wb_data_frame__.iterrows():
            # update status message if defined
            if status_callback and (current_entry % 100 == 0):
                status_callback("Process entry <strong>%s</strong> of "
                                "<strong>%s</strong>..." % (current_entry, amount_of_entries))

            faulty_entry = False
            msg = "import successful"
            p, created = Product.objects.get_or_create(product_id=row["product id"])
            changed = created

            # apply changes (only if a value is set, otherwise ignore it)
            try:
                if not pd.isnull(row["description"]):
                    if p.description != row["description"]:
                        p.description = row["description"]
                        changed = True

            except Exception as ex:
                faulty_entry = True
                msg = "cannot set description for <code>%s</code> (%s)" % (row["product id"], ex)

            try:
                if not pd.isnull(row["list price"]):
                    if p.list_price != float(row["list price"]):
                        p.list_price = row["list price"]
                        changed = True

            except Exception as ex:
                faulty_entry = True
                msg = "cannot set list price for <code>%s</code> (%s)" % (row["product id"], ex)

            try:
                if not pd.isnull(row["currency"]):
                    if p.currency != row["currency"]:
                        p.currency = row["currency"]
                        changed = True

            except Exception as ex:
                faulty_entry = True
                msg = "cannot set currency for <code>%s</code> (%s)" % (row["product id"], ex)

            try:
                # set vendor to unassigned (ID 0) if no Vendor is provided and the product was created
                if pd.isnull(row["vendor"]) and created:
                    v = Vendor.objects.get(id=0)
                    changed = True
                    p.vendor = v

                elif not pd.isnull(row["vendor"]):
                    if p.vendor.name != row["vendor"]:
                        try:
                            v = Vendor.objects.get(name=row["vendor"])

                        except Vendor.DoesNotExist:
                            raise Exception("Vendor <strong>%s</strong> doesn't exist" % row["vendor"])

                        changed = True
                        p.vendor = v

            except Exception as ex:
                faulty_entry = True
                msg = "cannot set vendor for <code>%s</code> (%s)" % (row["product id"], ex)

            # save result to database if any
            try:
                if changed:
                    # update element and add revision note
                    with transaction.atomic(), reversion.create_revision():
                        p.save()
                        if self.user_for_revision:
                            try:
                                reversion.set_user(self.user_for_revision)

                            except:
                                logger.warn("Cannot find username <strong>%s</strong> in database" % self.user_for_revision)

                        reversion.set_comment("manual product import")

                    self.valid_imported_products += 1
                    # add import result message
                    if created:
                        self.import_result_messages.append("product <code>%s</code> created" % p.product_id)

                    else:
                        self.import_result_messages.append("product <code>%s</code> updated" % p.product_id)

                else:
                    self.import_result_messages.append("<i>no changes for product "
                                                       "<code>%s</code> required</i>" % p.product_id)

            except Exception as ex:
                faulty_entry = True
                msg = "cannot save data for <code>%s</code> (%s)" % (row["product id"], ex)

            if faulty_entry:
                logger.error(msg)
                self.import_result_messages.append(msg)
                self.invalid_products += 1

                # terminate the process after 30 errors
                if self.invalid_products > 30:
                    self.import_result_messages.append("There are too many errors in your file, please "
                                                       "correct them and upload it again")
                    break

            current_entry += 1
