import json
import logging

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import URLValidator
from django.utils.datetime_safe import datetime
from app.ciscoeox.exception import ConnectionFailedException, CiscoApiCallFailed
from app.ciscoeox.base_api import CiscoEoxApi
from app.config.settings import AppSettings
from app.productdb.models import Product, Vendor, ProductMigrationSource, ProductMigrationOption

logger = logging.getLogger("productdb")


def convert_time_format(date_format):
    """
    helper function to convert the data format that is used by the Cisco EoX API
    :param date_format:
    :return:
    """
    if date_format == "YYYY-MM-DD":
        return "%Y-%m-%d"

    return "%Y-%m-%d"


def clean_api_url_response(url_response):
    """
    clean the string to a valid URL field (used with API data, because sometimes there are multiple or entries
    """
    clean_response = url_response.strip()
    if url_response != "":
        clean_response = clean_response if ";" not in clean_response else clean_response.split(";")[0]
        clean_response = clean_response if " or http://" not in clean_response \
            else clean_response.split(" or http://")[0]
        clean_response = clean_response if " and http://" not in clean_response \
            else clean_response.split(" and http://")[0]
        clean_response = clean_response if " http://" not in clean_response \
            else clean_response.split(" http://")[0]
        clean_response = clean_response if " and https://" not in clean_response \
            else clean_response.split(" and https://")[0]
        clean_response = clean_response if " or https://" not in clean_response \
            else clean_response.split(" or https://")[0]
        clean_response = clean_response if " https://" not in clean_response \
            else clean_response.split(" https://")[0]
    return clean_response


def update_local_db_based_on_record(eox_record, create_missing=False):
    """
    update a database entry based on an EoX record provided by the Cisco EoX API

    :param eox_record: JSON data from the Cisco EoX API
    :param create_missing: set to True, if the product should be created if it's not part of the local database
    :return: returns an error message or None if successful
    """
    pid = eox_record['EOLProductID']
    # only used with Cisco Products
    v = Vendor.objects.get(name="Cisco Systems")

    if create_missing:
        product, created = Product.objects.get_or_create(
            product_id=pid,
            vendor=v
        )

    else:
        try:
            product = Product.objects.get(
                product_id=pid,
                vendor=v
            )
            created = False

        except ObjectDoesNotExist:
            logger.debug("%15s: Product not found in database (create disabled)" % pid, exc_info=True)
            return None

    if created:
        product.product_id = pid
        product.description = eox_record['ProductIDDescription']
        # it is a Cisco API and the vendors are predefined in the database
        product.vendor = v
        logger.debug("%15s: Product created" % pid)

    # update the lifecycle information
    try:
        logger.debug("%15s: update product lifecycle values" % pid)

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
                value = value.strip() if value else ""
                if value != "":
                    setattr(
                        product,
                        value_map[key],
                        datetime.strptime(
                            value,
                            convert_time_format(eox_record[key].get("dateFormat", "%Y-%m-%d"))
                        ).date()
                    )

                else:
                    # required if date is removed after an earlier sync
                    setattr(
                        product,
                        value_map[key],
                        None
                    )

        # save string values from Cisco EoX API record
        if "LinkToProductBulletinURL" in eox_record.keys():
            value = clean_api_url_response(eox_record.get('LinkToProductBulletinURL', ""))
            if value != "":
                val = URLValidator()
                try:
                    val(value)
                    product.eol_reference_url = value

                except ValidationError:
                    raise Exception("invalid EoL reference URL")

                if "ProductBulletinNumber" in eox_record.keys():
                    product.eol_reference_number = eox_record.get('ProductBulletinNumber', "EoL bulletin")

        product.save()

    except Exception as ex:
        if created:
            # remove the new (incomplete) entry from the database
            product.delete()

        logger.error("%15s: Product Data update failed." % pid, exc_info=True)
        logger.debug("%15s: DataSet with exception\n%s" % (pid, json.dumps(eox_record, indent=4)))
        return "Product Data update failed: %s" % str(ex)

    # save migration information if defined
    if "EOXMigrationDetails" in eox_record:
        migration_details = eox_record["EOXMigrationDetails"]
        product_migration_source, created = ProductMigrationSource.objects.get_or_create(
            name="Cisco EoX Migration option"
        )

        if created:
            product_migration_source.description = "Migration option suggested by the Cisco EoX API."
            product_migration_source.save()

        if "MigrationOption" in migration_details:
            candidate_replacement_pid = migration_details["MigrationProductId"].strip()

            if candidate_replacement_pid == pid:
                logger.error("Product ID '%s' should be replaced by itself, which is not possible" % pid)

            else:
                # only a single migration option per migration source is allowed
                pmo, _ = ProductMigrationOption.objects.get_or_create(product=product,
                                                                      migration_source=product_migration_source)
                if migration_details["MigrationOption"] == "Enter PID(s)":
                    # product replacement available, add replacement PID
                    pmo.replacement_product_id = candidate_replacement_pid
                    pmo.migration_product_info_url = clean_api_url_response(migration_details["MigrationProductInfoURL"])

                elif migration_details["MigrationOption"] == "See Migration Section" or \
                        migration_details["MigrationOption"] == "Enter Product Name(s)":
                    # complex product migration, only add comment
                    mig_strat = migration_details["MigrationStrategy"].strip()
                    pmo.comment = mig_strat if mig_strat != "" else migration_details["MigrationProductName"].strip()
                    pmo.migration_product_info_url = clean_api_url_response(migration_details["MigrationProductInfoURL"])

                else:
                    # no replacement available, only add comment
                    pmo.comment = migration_details["MigrationOption"].strip()  # some data separated by blank
                    pmo.migration_product_info_url = clean_api_url_response(migration_details["MigrationProductInfoURL"])

                # add message if only a single entry was saved
                if pmo.migration_product_info_url != migration_details["MigrationProductInfoURL"].strip():
                    return "Multiple URL values from the Migration Note received, only the first one is saved"

                pmo.save()


def get_raw_api_data(api_query=None, year=None):
    """
    returns all EoX records for a specific query (from all pages)
    :param api_query: single query that is send to the Cisco EoX API
    :param year: get all EoX data that are announced in a specific year
    :raises CiscoApiCallFailed: exception raised if Cisco EoX API call failed
    :return: list that contains all EoX records from the Cisco EoX API
    """
    if api_query is None and year is None:
        raise ValueError("either year or the api_query must be provided")

    if api_query:
        if type(api_query) is not str:
            raise ValueError("api_query must be a string value")

    if year:
        if type(year) is not int:
            raise ValueError("year must be an integer value")

    # load application settings and check, that the API is enabled
    app_settings = AppSettings()

    if not app_settings.is_cisco_api_enabled():
        msg = "Cisco API access not enabled"
        logger.warning(msg)
        raise CiscoApiCallFailed(msg)

    # start Cisco EoX API query
    logger.info("send query to Cisco EoX database: %s" % api_query)

    eoxapi = CiscoEoxApi()
    eoxapi.load_client_credentials()
    results = []

    try:
        current_page = 1
        result_pages = 999

        while current_page <= result_pages:
            logger.info("Executing API query %s on page '%d" % ('%s' % api_query if api_query else "for year %d" % year, current_page))

            # will raise a CiscoApiCallFailed exception on error
            if year:
                eoxapi.query_year(year_to_query=year, page=current_page)

            else:
                eoxapi.query_product(product_id=api_query, page=current_page)

            result_pages = eoxapi.amount_of_pages()

            if eoxapi.get_page_record_count() > 0:
                results.extend(eoxapi.get_eox_records())

            current_page += 1

    except ConnectionFailedException:
        logger.error("Query failed, server not reachable: %s" % api_query, exc_info=True)
        raise

    except CiscoApiCallFailed:
        logger.fatal("Query failed: %s" % api_query, exc_info=True)
        raise

    logger.debug("found %d records for year %s" % (len(results), year))

    return results
