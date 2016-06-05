import json
import logging
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


def update_local_db_based_on_record(eox_record, create_missing=False):
    """
    update a database record based on a Cisco EoX API call

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
            logger.info("Product '%s' was not in database and is created" % pid)
            product.product_id = pid
            product.description = eox_record['ProductIDDescription']
            # it is a Cisco API and the vendors are read-only within the database
            product.vendor = Vendor.objects.get(name="Cisco Systems")
            result_record["created"] = True
    else:
        try:
            product = Product.objects.get(product_id=pid)

        except Exception:
            logger.debug("product not found in database: %s" % pid, exc_info=True)
            result_record["created"] = False
            return result_record

    # update the lifecycle information
    try:
        update = True
        if product.eox_update_time_stamp is None:
            logger.info("Update product %s because of missing timestamps" % pid)
            result_record["updated"] = True

        else:
            date_format = convert_time_format(eox_record['UpdatedTimeStamp']['dateFormat'])
            updated_time_stamp = datetime.strptime(eox_record['UpdatedTimeStamp']['value'],
                                                   date_format).date()
            if product.eox_update_time_stamp >= updated_time_stamp:
                logger.debug("update of product not required: %s >= %s " % (product.eox_update_time_stamp,
                                                                            updated_time_stamp))
                result_record["updated"] = False
                result_record["message"] = "update suppressed (data not modified)"
                update = False

            else:
                logger.info("Product %s update required" % pid)
                result_record["updated"] = True

        if update:
            if "UpdatedTimeStamp" in eox_record.keys():
                value = eox_record['UpdatedTimeStamp']['value']
                if value != " ":
                    euts = datetime.strptime(value,
                                             convert_time_format(
                                                 eox_record['UpdatedTimeStamp']['dateFormat']
                                             )).date()
                    product.eox_update_time_stamp = euts

            if "EndOfSaleDate" in eox_record.keys():
                value = eox_record['EndOfSaleDate']['value']
                if value != " ":
                    eosd = datetime.strptime(value,
                                             convert_time_format(
                                                 eox_record['EndOfSaleDate']['dateFormat']
                                             )).date()
                    product.end_of_sale_date = eosd

            if "LastDateOfSupport" in eox_record.keys():
                value = eox_record['LastDateOfSupport']['value']
                if value != " ":
                    eosud = datetime.strptime(value,
                                              convert_time_format(
                                                  eox_record['LastDateOfSupport']['dateFormat']
                                              )).date()
                    product.end_of_support_date = eosud

            if "EOXExternalAnnouncementDate" in eox_record.keys():
                value = eox_record['EOXExternalAnnouncementDate']['value']
                if value != " ":
                    eead = datetime.strptime(value,
                                             convert_time_format(
                                                 eox_record['EOXExternalAnnouncementDate']['dateFormat']
                                             )).date()
                    product.eol_ext_announcement_date = eead

            if "EndOfSWMaintenanceReleases" in eox_record.keys():
                value = eox_record['EndOfSWMaintenanceReleases']['value']
                if value != " ":
                    eosmd = datetime.strptime(value,
                                              convert_time_format(
                                                  eox_record['EndOfSWMaintenanceReleases']['dateFormat']
                                              )).date()
                    product.end_of_sw_maintenance_date = eosmd

            if "EndOfRoutineFailureAnalysisDate" in eox_record.keys():
                value = eox_record['EndOfRoutineFailureAnalysisDate']['value']
                if value != " ":
                    eorfa_date = datetime.strptime(value,
                                                   convert_time_format(
                                                       eox_record['EndOfRoutineFailureAnalysisDate']['dateFormat']
                                                   )).date()
                    product.end_of_routine_failure_analysis = eorfa_date

            if "EndOfServiceContractRenewal" in eox_record.keys():
                value = eox_record['EndOfServiceContractRenewal']['value']
                if value != " ":
                    eoscr = datetime.strptime(value,
                                              convert_time_format(
                                                  eox_record['EndOfServiceContractRenewal']['dateFormat']
                                              )).date()
                    product.end_of_service_contract_renewal = eoscr

            if "EndOfSvcAttachDate" in eox_record.keys():
                value = eox_record['EndOfSvcAttachDate']['value']
                if value != " ":
                    eonsa = datetime.strptime(value,
                                              convert_time_format(
                                                  eox_record['EndOfSvcAttachDate']['dateFormat']
                                              )).date()
                    product.end_of_new_service_attachment_date = eonsa

            if "EndOfSecurityVulSupportDate" in eox_record.keys():
                value = eox_record['EndOfSecurityVulSupportDate']['value']
                if value != " ":
                    eovsd = datetime.strptime(value,
                                              convert_time_format(
                                                  eox_record['EndOfSecurityVulSupportDate']['dateFormat']
                                              )).date()
                    product.end_of_sec_vuln_supp_date = eovsd

            if "ProductBulletinNumber" in eox_record.keys():
                product.eol_reference_number = eox_record['ProductBulletinNumber']

            if "LinkToProductBulletinURL" in eox_record.keys():
                product.eol_reference_url = eox_record['LinkToProductBulletinURL']

            product.save()

    except Exception as ex:
        logger.error("update of product '%s' failed." % pid, exc_info=True)
        logger.debug("DataSet with exception\n%s" % json.dumps(eox_record, indent=4))
        result_record["message"] = "Update failed: %s" % str(ex)
        return result_record

    return result_record


def query_cisco_eox_api(query_string, blacklist, create_missing=False):
    """
    execute a query against the Cisco API and updates the local database if the product
    is not defined as blacklisted.
    :param query_string: query that is executed
    :param blacklist: list of strings that shouldn't be imported to the database
    :param create_missing:
    :return:
    """
    eoxapi = CiscoEoxApi()
    eoxapi.load_client_credentials()
    results = []

    try:
        max_pages = 999
        current_page = 1
        result_pages = 0

        while current_page <= max_pages:
            logger.info("Executing API query '%s' on page '%d" % (query_string, current_page))
            eoxapi.query_product(product_id=query_string, page=current_page)
            if current_page == 1:
                result_pages = eoxapi.amount_of_pages()
                logger.info("Initial query returns %d page(s)" % result_pages)

            records = eoxapi.get_eox_records()

            # check for errors
            if eoxapi.has_error(records[0]):
                logger.info("Query '%s' returns no valid values: %s" % (query_string,
                                                                        eoxapi.get_error_description(records[0])))
            else:
                # check that the query has valid results
                if eoxapi.get_valid_record_count() > 0:
                    # processing records
                    for record in records:
                        result_record = {}
                        pid = record['EOLProductID']
                        result_record["PID"] = pid
                        result_record["created"] = False
                        result_record["updated"] = False
                        result_record["message"] = None
                        logger.info("processing product '%s'..." % pid)

                        # check if record is product of the blacklist
                        if pid not in blacklist:
                            res = update_local_db_based_on_record(record, create_missing)
                            res["blacklist"] = False
                            result_record.update(res)

                        else:
                            logger.info("Product '%s' blacklisted... no further processing" % pid)
                            result_record.update({
                                "blacklist": True
                            })

                        results.append(result_record)

                else:
                    logger.warn("Query '%s' returns no valid values" % query_string)

            if current_page == result_pages:
                break

            else:
                current_page += 1

    except ConnectionFailedException:
        logger.error("connection for query failed: %s" % query_string, exc_info=True)
        raise

    except CiscoApiCallFailed:
        logger.fatal("query failed: %s" % query_string, exc_info=True)
        raise

    return results


def update_cisco_eox_database(api_query):
    """
    Synchronizes the local EoX data from the Cisco EoX API using the specified queries or the queries specified in the
    configuration when api_query is set to None
    :param api_query: single query that is send to the Cisco EoX API
    :return:
    """
    # load application settings and check, that the API is enabled
    app_settings = AppSettings()
    app_settings.read_file()

    if not app_settings.is_cisco_api_enabled():
        msg = "Cisco API access not enabled"
        logger.warn(msg)
        raise CiscoApiCallFailed(msg)

    blacklist = app_settings.get_product_blacklist_regex().split(";")
    create_missing = app_settings.is_auto_create_new_products()

    # start with Cisco EoX API queries
    logger.info("Query EoX database: %s" % api_query)
    query_results = query_cisco_eox_api(api_query, blacklist, create_missing)

    # filter empty result strings
    if len(query_results) == 0:
        query_results = [
            {
                "PID": None,
                "blacklist": False,
                "updated": False,
                "created": False,
                "message": "No product update required"
            }
        ]

    return query_results
