import re
import json
import logging
from reversion import revisions as reversion
from django.db import transaction
from django.utils.datetime_safe import datetime
from app.ciscoeox.exception import ConnectionFailedException, CiscoApiCallFailed
from app.ciscoeox.base_api import CiscoEoxApi
from app.config import AppSettings
from app.productdb.models import Product, Vendor

logger = logging.getLogger(__name__)


def convert_time_format(date_format):
    """
    helper function to convert the data format that is used by the Cisco EoX API
    :param date_format:
    :return:
    """
    if date_format == "YYYY-MM-DD":
        return "%Y-%m-%d"

    return "%Y-%m-%d"


def product_id_in_database(product_id):
    """
    checks that the Product ID is stored in the database
    """
    try:
        result = Product.objects.filter(product_id=product_id)
        if len(result) == 0:
            return False
        else:
            return True
    except:
        logger.debug("Cannot find product %s in database" % product_id, exc_info=True)
        return False


def update_local_db_based_on_record(eox_record, create_missing=False):
    """
    update a database record based on a record provided by the Cisco EoX API

    :param eox_record: JSON data from the Cisco EoX API
    :param create_missing: set to True, if the product should be created if it doesn't exist in the local database
    :return:
    """
    pid = eox_record['EOLProductID']
    result_record = {
        "PID": pid,
        "blacklist": False,
        "updated": False,
        "created": False,
        "message": None
    }

    if create_missing:
        product, created = Product.objects.get_or_create(product_id=pid)
        if created:
            logger.debug("Product '%s' was not in database and is created" % pid)
            product.product_id = pid
            product.description = eox_record['ProductIDDescription']
            # it is a Cisco API and the vendors are read-only within the database
            product.vendor = Vendor.objects.get(name="Cisco Systems")
            result_record["created"] = True
    else:
        try:
            created = False
            product = Product.objects.get(product_id=pid)

        except Exception:
            logger.info("product not found in database: %s" % pid, exc_info=True)
            result_record["created"] = False
            return result_record

    # update the lifecycle information
    try:
        update = True
        if product.eox_update_time_stamp is None:
            logger.debug("Update product %s because of missing timestamps" % pid)
            result_record["updated"] = True

        else:
            date_format = convert_time_format(eox_record['UpdatedTimeStamp']['dateFormat'])
            updated_time_stamp = datetime.strptime(eox_record['UpdatedTimeStamp']['value'], date_format).date()

            if product.eox_update_time_stamp >= updated_time_stamp:
                logger.debug("update of product not required: %s >= %s " % (product.eox_update_time_stamp,
                                                                            updated_time_stamp))
                result_record["updated"] = False
                result_record["message"] = "update suppressed (data not modified)"
                update = False

            else:
                logger.debug("Product %s update required" % pid)
                result_record["updated"] = True

        if update:
            # save datetime values from Cisco EoX API record
            value_map = {
                # <API value> : <class attribute>
                "UpdatedTimeStamp": "eox_update_time_stamp",
                "EndOfSaleDate": "end_of_sale_date",
                "LastDateOfSupport": "end_of_support_date",
                "EOXExternalAnnouncementDate": "eol_ext_announcement_date",
                "EndOfSWMaintenanceReleases": "end_of_sw_maintenance_date",
                "EndOfRoutineFailureAnalysisDate": "end_of_routine_failure_analysis",
                "EndOfServiceContractRenewal": "end_of_service_contract_renewal",
                "EndOfSvcAttachDate": "end_of_new_service_attachment_date",
                "EndOfSecurityVulSupportDate": "end_of_sec_vuln_supp_date",
            }

            for key in value_map.keys():
                if eox_record.get(key, None):
                    value = eox_record[key].get("value", None)
                    if value != " ":
                        setattr(
                            product,
                            value_map[key],
                            datetime.strptime(
                                value,
                                convert_time_format(eox_record[key].get("dateFormat", "%Y-%m-%d"))
                            ).date()
                        )

            # save string values from Cisco EoX API record
            if "LinkToProductBulletinURL" in eox_record.keys():
                product.eol_reference_url = eox_record.get('LinkToProductBulletinURL', "")
                if ("ProductBulletinNumber" in eox_record.keys()) and (product.eol_reference_url != ""):
                    product.eol_reference_number = eox_record.get('ProductBulletinNumber', "EoL bulletin")

            with transaction.atomic(), reversion.create_revision():
                product.save()
                reversion.set_comment("Updated by the Cisco EoX API crawler")

    except Exception as ex:
        if created:
            # remove the new (incomplete) entry from the database
            product.delete()

        logger.error("update of product '%s' failed." % pid, exc_info=True)
        logger.debug("DataSet with exception\n%s" % json.dumps(eox_record, indent=4))
        result_record["message"] = "Update failed: %s" % str(ex)
        return result_record

    return result_record


def update_cisco_eox_database(api_query):
    """
    synchronizes the local database with the Cisco EoX API using the specified query
    :param api_query: single query that is send to the Cisco EoX API
    :raises CiscoApiCallFailed: exception raised if Cisco EoX API call failed
    :return: list of dictionary that describe the updates to the database
    """
    if type(api_query) is not str:
        raise ValueError("api_query must be a string value")

    # load application settings and check, that the API is enabled
    app_settings = AppSettings()
    app_settings.read_file()

    if not app_settings.is_cisco_api_enabled():
        msg = "Cisco API access not enabled"
        logger.warn(msg)
        raise CiscoApiCallFailed(msg)

    blacklist_raw_string = app_settings.get_product_blacklist_regex()
    create_missing = app_settings.is_auto_create_new_products()

    # clean blacklist string and remove empty statements
    # (split lines, if any and split the string by semicolon)
    blacklist = []
    for e in [e.split(";") for e in blacklist_raw_string.splitlines()]:
        blacklist += e
    blacklist = [e for e in blacklist if e != ""]

    # start Cisco EoX API query
    logger.info("Query EoX database: %s" % api_query)

    eoxapi = CiscoEoxApi()
    eoxapi.load_client_credentials()
    results = []

    try:
        max_pages = 999
        current_page = 1
        result_pages = 0

        while current_page <= max_pages:
            logger.info("Executing API query '%s' on page '%d" % (api_query, current_page))
            # will raise a CiscoApiCallFailed exception on error
            eoxapi.query_product(product_id=api_query, page=current_page)
            if current_page == 1:
                result_pages = eoxapi.amount_of_pages()
                logger.info("Initial query returns %d page(s)" % result_pages)

            records = eoxapi.get_eox_records()

            # check that the query has valid results
            if eoxapi.get_page_record_count() > 0:
                # processing records
                for record in records:
                    result_record = {}
                    pid = record['EOLProductID']
                    result_record["PID"] = pid
                    result_record["created"] = False
                    result_record["updated"] = False
                    result_record["message"] = None
                    logger.info("processing product '%s'..." % pid)

                    pid_in_database = product_id_in_database(pid)

                    # check if the product ID is blacklisted by a regular expression
                    pid_blacklisted = False
                    for regex in blacklist:
                        try:
                            if re.search(regex, pid, re.I):
                                pid_blacklisted = True
                                break
                        except:
                            # silently ignore the issue, invalid regular expressions are handled by the settings form
                            logger.info("invalid regular expression: %s" % regex)

                    # ignore if the product id is not in the database
                    if pid_blacklisted and not pid_in_database:
                        logger.info("Product '%s' blacklisted... no further processing" % pid)
                        result_record.update({
                            "blacklist": True
                        })

                    else:
                        res = update_local_db_based_on_record(record, create_missing)
                        res["blacklist"] = False
                        result_record.update(res)

                    results.append(result_record)

            if current_page == result_pages:
                break

            else:
                current_page += 1

        # filter empty result strings
        if len(results) == 0:
            results = [
                {
                    "PID": None,
                    "blacklist": False,
                    "updated": False,
                    "created": False,
                    "message": "No product update required"
                }
            ]

    except ConnectionFailedException:
        logger.error("Query failed, server not reachable: %s" % api_query, exc_info=True)
        raise

    except CiscoApiCallFailed:
        logger.fatal("Query failed: %s" % api_query, exc_info=True)
        raise

    return results
