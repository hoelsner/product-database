import datetime
import logging
import pandas as pd
from django.db import transaction
from reversion import revisions as reversion
from xlrd import XLRDError
from app.productdb.models import Product, CURRENCY_CHOICES
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
        )

        # normalize the column names (all lowercase, strip whitespace if any)
        self.__wb_data_frame__.columns = [x.lower() for x in self.__wb_data_frame__.columns]
        self.__wb_data_frame__.columns = [x.strip() for x in self.__wb_data_frame__.columns]

        # drop all values that are null in the product id column
        self.__wb_data_frame__.dropna(axis=0, subset=["product id"], inplace=True)

    def verify_file(self):
        if self.workbook is None:
            self.__load_workbook__()
        self.valid_file = False

        sheets = self.workbook.sheet_names
        required_sheet = "products"
        required_keys = {"product id", "description", "list price", "vendor"}

        # verify worksheet that is required
        if required_sheet not in sheets:
            raise InvalidImportFormatException("sheet '%s' not found" % required_sheet)

        # verify keys in file
        dframe = self.workbook.parse("products")
        keys = [x.lower() for x in set(dframe.keys())]

        if len(required_keys.intersection(keys)) != len(required_keys):
            raise InvalidImportFormatException("required keys not found in Excel file")

        self.valid_file = True

    @property
    def amount_of_products(self):
        if self.__wb_data_frame__ is None:
            self.__create_data_frame__()
        return len(self.__wb_data_frame__)

    def is_valid_file(self):
        return self.valid_file

    def _import_datetime_column_from_file(self, row_key, row, target_key, product):
        """
        helper method to import an optional column from the excel file
        """
        changed = False
        faulty_entry = False
        msg = ""
        try:
            if row_key in row:
                if not pd.isnull(row[row_key]):
                    currval = getattr(product, target_key)
                    if (type(row[row_key]) is pd.tslib.Timestamp) or (type(row[row_key]) is datetime.datetime):
                        newval = row[row_key].date()

                    else:
                        newval = None

                    if currval != newval:
                        setattr(product, target_key, row[row_key].date())
                        changed = True

        except Exception as ex:
            faulty_entry = True
            msg = "cannot set %s for <code>%s</code> (%s)" % (row_key, row["product id"], ex)

        return changed, faulty_entry, msg

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
            row_key = "description"
            try:
                # set the description value
                if not pd.isnull(row[row_key]):
                    if p.description != row[row_key]:
                        p.description = row[row_key]
                        changed = True

                # determine the list price and currency from the excel file
                row_key = "list price"
                new_currency = "USD"    # default in model

                if not pd.isnull(row[row_key]):
                    if type(row[row_key]) == float:
                        new_price = row[row_key]

                    elif type(row[row_key]) == str:
                        price = row[row_key].split(" ")
                        if len(price) == 1:
                            new_price = float(row[row_key])

                        elif len(price) == 2:
                            try:
                                new_price = float(price[0])
                            except:
                                raise Exception("cannot convert price information to float")

                            # check valid currency value
                            valid_currency = True if price[1].upper() in dict(CURRENCY_CHOICES).keys() else False
                            if valid_currency:
                                new_currency = price[1].upper()

                            else:
                                raise Exception("cannot set currency unknown value %s" % price[1].upper())

                        else:
                            raise Exception("invalid format for list price, detected multiple spaces")

                    else:
                        logger.debug("list price data type for %s identified as %s" % (
                            row["product id"],
                            str(type(row[row_key]))
                        ))
                        raise Exception("invalid data-type for list price")
                else:
                    new_price = None

                row_key = "currency"
                if row_key in row:
                    if not pd.isnull(row[row_key]):
                        # check valid currency value
                        valid_currency = True if row[row_key].upper() in dict(CURRENCY_CHOICES).keys() else False
                        if valid_currency:
                            new_currency = row[row_key].upper()

                        else:
                            raise Exception("cannot set currency unknown value %s" % row[row_key].upper())

                # apply the new list price and currency if required
                if p.list_price != new_price:
                    p.list_price = new_price
                    changed = True
                if p.currency != new_currency:
                    p.currency = new_currency
                    changed = True

                # set vendor to unassigned (ID 0) if no Vendor is provided and the product was created
                row_key = "vendor"
                if pd.isnull(row[row_key]) and created:
                    v = Vendor.objects.get(id=0)
                    changed = True
                    p.vendor = v

                elif not pd.isnull(row[row_key]):
                    if p.vendor.name != row[row_key]:
                        try:
                            v = Vendor.objects.get(name=row[row_key])

                        except Vendor.DoesNotExist:
                            raise Exception("Vendor <strong>%s</strong> doesn't exist" % row[row_key])

                        changed = True
                        p.vendor = v

                # set Eol note URL and friendly name (both optional)
                row_key = "eol note url"
                if row_key in row:
                    if not pd.isnull(row[row_key]):
                        if p.eol_reference_url != row[row_key]:
                            p.eol_reference_url = row[row_key]
                            changed = True

                row_key = "eol note url (friendly name)"
                if row_key in row:
                    if not pd.isnull(row[row_key]):
                        if p.eol_reference_number != row[row_key]:
                            p.eol_reference_number = row[row_key]

            except Exception as ex:
                faulty_entry = True
                msg = "cannot set %s for <code>%s</code> (%s)" % (row_key, row["product id"], ex)

            # import datetime columns from file
            data_map = {
                # product attribute - data frame column name (lowered during the import)
                "eox_update_time_stamp": "eox update timestamp",
                "eol_ext_announcement_date": "eol announcement date",
                "end_of_sale_date": "end of sale date",
                "end_of_new_service_attachment_date": "end of new service attachment date",
                "end_of_sw_maintenance_date": "end of sw maintenance date",
                "end_of_routine_failure_analysis": "end of routing failure analysis date",
                "end_of_service_contract_renewal": "end of service contract renewal date",
                "end_of_support_date": "last date of support",
                "end_of_sec_vuln_supp_date": "end of security/vulnerability support date"
            }

            for key in data_map.keys():
                c, f, ret_msg = self._import_datetime_column_from_file(data_map[key], row, key, p)
                if c:
                    # value was changed
                    changed = True
                if f:
                    # value was faulty
                    msg = ret_msg
                    faulty_entry = True
                    break

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
                msg = "cannot save data for <code>%s</code> in database (%s)" % (row["product id"], ex)

            if faulty_entry:
                logger.error("cannot import %s (%s)" % (row["product id"], msg))
                self.import_result_messages.append(msg)
                self.invalid_products += 1

                # terminate the process after 30 errors
                if self.invalid_products > 30:
                    self.import_result_messages.append("There are too many errors in your file, please "
                                                       "correct them and upload it again")
                    break

            current_entry += 1
