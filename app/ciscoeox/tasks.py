import logging
import re
import time
from celery import chain
from django.core.cache import cache
from django.db import transaction
from django.core.exceptions import ValidationError
from cacheops import invalidate_model

import app.ciscoeox.api_crawler as cisco_eox_api_crawler
from app.ciscoeox.exception import CiscoApiCallFailed
from app.config.settings import AppSettings
from app.config.models import NotificationMessage
from app.config import utils
from app.productdb.models import Vendor, Product
from django_project.celery import app as app, TaskState

logger = logging.getLogger("productdb")

NOTIFICATION_MESSAGE_TITLE = "Synchronization with Cisco EoX API"


@app.task(name="ciscoeox.populate_product_lc_state_sync_field")
def cisco_eox_populate_product_lc_state_sync_field():
    """
    Periodic job to populate the lc_state_sync field in the Products, which shows that the product lifecycle data are
    automatically synchronized against the Cisco EoX API in this case
    :return:
    """
    try:
        cis_vendor = Vendor.objects.get(name__istartswith="Cisco")

    except:
        # Vendor doesn't exist, no steps required
        logger.fatal("Vendor \"Cisco Systems\" not found in database, please check your installation")
        return {"error": "Vendor \"Cisco Systems\" not found in database"}

    cisco_products = Product.objects.filter(vendor=cis_vendor)

    if cisco_products.count() != 0:
        app_config = AppSettings()
        queries = app_config.get_cisco_eox_api_queries_as_list()

        # escape the query strings
        queries = [re.escape(e) for e in queries]

        # convert the wildcard values
        queries = [e.replace("\\*", ".*") for e in queries]
        queries = ["^" + e + "$" for e in queries]

        with transaction.atomic():
            # reset all entries for the vendor
            Product.objects.filter(vendor=cis_vendor).update(lc_state_sync=False)

            # only set the state sync to true if the periodic synchronization is enabled
            if app_config.is_periodic_sync_enabled():
                for query in queries:
                    Product.objects.filter(product_id__regex=query, vendor=cis_vendor).update(lc_state_sync=True)

        invalidate_model(Product)

        return {"status": "Database updated"}

    else:
        return {"error": "No Products associated to \"Cisco Systems\" found in database"}


@app.task(
    serializer="json",
    name="ciscoeox.update_local_database_records"
)
def update_local_database_records(results, year, records):
    for record in records:
        cisco_eox_api_crawler.update_local_db_based_on_record(record, True)

    results[str(year)] = "success"
    return results


@app.task(
    serializer="json",
    name="ciscoeox.notify_initial_import_result"
)
def notify_initial_import_result(results):
    msg = "The following years were successful imported: " + ",".join(results.keys())

    NotificationMessage.objects.create(
        title="Initial data import finished",
        summary_message=msg,
        detailed_message=msg,
        type=NotificationMessage.MESSAGE_INFO
    )


@app.task(
    serializer="json",
    name="ciscoeox.initial_sync_with_cisco_eox_api",
    bind=True
)
def initial_sync_with_cisco_eox_api(self, years_list):
    """
    synchronize all entries from the EoX API for a given amount of years (today - n-years), ignores the create missing
    entries and the configurable blacklist.
    :param self:
    :param years_list: list of years to sync (e.g. [2018, 2017, 2016]
    :return:
    """
    if type(years_list) is not list:
        raise AttributeError("years_list must be a list")

    for val in years_list:
        if type(val) is not int:
            raise AttributeError("years_list must be a list of integers")

    if len(years_list) == 0:
        return {
            "status_message": "No years provided, nothing to do."
        }

    app_config = AppSettings()

    # test Cisco EoX API access
    test_result = utils.check_cisco_eox_api_access(
        app_config.get_cisco_api_client_id(),
        app_config.get_cisco_api_client_secret(),
        False
    )
    failed_years = []
    successful_years = []

    if test_result:
        # perform synchronization
        self.update_state(state=TaskState.PROCESSING, meta={
            "status_message": "start initial synchronization with the Cisco EoX API..."
        })
        all_records = []
        for year in years_list:
            self.update_state(state=TaskState.PROCESSING, meta={
                "status_message": "fetch all information for year %d..." % year
            })
            # wait some time between the query calls
            time.sleep(int(app_config.get_cisco_eox_api_sync_wait_time()))

            # fetch all API entries for a specific year
            try:
                records = cisco_eox_api_crawler.get_raw_api_data(year=year)
                successful_years += [year]

                all_records.append({
                    "year": year,
                    "records": records
                })

            except CiscoApiCallFailed as ex:
                msg = "Cisco EoX API call failed (%s)" % str(ex)
                logger.error("Query for year %s to Cisco EoX API failed (%s)" % (year, msg), exc_info=True)
                failed_years += [year]

                NotificationMessage.objects.create(
                    title="Initial data import failed",
                    summary_message="Unable to collect Cisco EoX data for year %d" % year,
                    detailed_message=msg,
                    type=NotificationMessage.MESSAGE_ERROR
                )

            except Exception as ex:
                msg = "Unexpected Exception, cannot access the Cisco API. Please ensure that the server is " \
                      "connected to the internet and that the authentication settings are valid."
                logger.error("Query for year %s to Cisco EoX API failed (%s)" % (year, msg), exc_info=True)
                failed_years += [year]

                NotificationMessage.objects.create(
                    title="Initial data import failed",
                    summary_message="Unable to collect Cisco EoX data for year %d" % year,
                    detailed_message=msg,
                    type=NotificationMessage.MESSAGE_ERROR
                )

        # update local database (asynchronous task)
        if len(all_records) != 0:
            tasks = [
                update_local_database_records.s({}, all_records[0]["year"], all_records[0]["records"])
            ]
            for r in all_records[1:]:
                tasks.append(update_local_database_records.s(r["year"], r["records"]))

            tasks.append(notify_initial_import_result.s())
            chain(*tasks).apply_async()

    time.sleep(10)
    # remove in progress flag with the cache
    cache.delete("CISCO_EOX_INITIAL_SYN_IN_PROGRESS")

    success_msg = ",".join([str(e) for e in successful_years])
    if len(success_msg) == 0:
        success_msg = "None"
    failed_msg = ""
    if len(failed_years) != 0:
        failed_msg = " (for %s the synchronization failed)" % ",".join([str(e) for e in failed_years])

    return {
        "status_message": "The EoX data were successfully downloaded for the following years: %s%s" % (success_msg,
                                                                                                       failed_msg)
    }


@app.task(
    serializer="json",
    name="ciscoeox.update_cisco_eox_records",
)
def update_cisco_eox_records(records):
    """
    update given database records from the Cisco EoX v5 API
    :param records:
    :return:
    """
    app_config = AppSettings()

    blacklist_raw_string = app_config.get_product_blacklist_regex()
    create_missing = app_config.is_auto_create_new_products()

    # build blacklist from configuration
    blacklist = []
    for e in [e.split(";") for e in blacklist_raw_string.splitlines()]:
        blacklist += e
    blacklist = [e for e in blacklist if e != ""]

    counter = 0
    messages = {}

    for record in records:
        blacklisted = False
        for regex in blacklist:
            try:
                if re.search(regex, record["EOLProductID"], re.I):
                    blacklisted = True
                    break

            except:
                logger.warning("invalid regular expression in blacklist: %s" % regex)

        if not blacklisted:
            try:
                message = cisco_eox_api_crawler.update_local_db_based_on_record(record, create_missing)
                if message:
                    messages[record["EOLProductID"]] = message

            except ValidationError as ex:
                logger.error("invalid data received from Cisco API, cannot save data object for "
                             "'%s' (%s)" % (record, str(ex)), exc_info=True)
        else:
            messages[record["EOLProductID"]] = " Product record ignored"

        counter += 1

    return {
        "count": counter,
        "messages": messages
    }


@app.task(
    serializer="json",
    name="ciscoeox.synchronize_with_cisco_eox_api",
    bind=True,
    soft_time_limit=82800,
    time_limit=86400
)
def execute_task_to_synchronize_cisco_eox_states(self, ignore_periodic_sync_flag=False):
    """
    This task synchronize the local database with the Cisco EoX API. It executes all configured queries and stores the
    results in the local database. There are two types of operation:
      * cisco_eox_api_auto_sync_auto_create_elements is set to true - will create any element which is not part of the
                                                                      blacklist and not in the database
      * cisco_eox_api_auto_sync_auto_create_elements is set to false - will only update entries, which are already
                                                                       included in the database
    :return:
    """
    app_config = AppSettings()
    run_task = app_config.is_periodic_sync_enabled()

    if not (run_task or ignore_periodic_sync_flag):
        result = {
            "status_message": "task not enabled"
        }

    else:
        logger.info("start sync with Cisco EoX API...")
        self.update_state(state=TaskState.PROCESSING, meta={
            "status_message": "sync with Cisco EoX API..."
        })

        # read configuration for the Cisco EoX API synchronization
        queries = app_config.get_cisco_eox_api_queries_as_list()

        if len(queries) == 0:
            result = {
                "status_message": "No Cisco EoX API queries configured."
            }

            NotificationMessage.objects.create(
                title=NOTIFICATION_MESSAGE_TITLE,
                type=NotificationMessage.MESSAGE_WARNING,
                summary_message="There are no Cisco EoX API queries configured. Nothing to do.",
                detailed_message="There are no Cisco EoX API queries configured. Please configure at least on EoX API "
                                 "query in the settings or disable the periodic synchronization."
            )

        # update the local database with the Cisco EoX API
        else:
            # test Cisco EoX API access
            test_result = utils.check_cisco_eox_api_access(
                app_config.get_cisco_api_client_id(),
                app_config.get_cisco_api_client_secret(),
                False
            )

            if not test_result:
                msg = "Cannot contact Cisco EoX API, please verify your internet connection and access " \
                      "credentials."
                if not ignore_periodic_sync_flag:
                    NotificationMessage.objects.create(
                        title=NOTIFICATION_MESSAGE_TITLE, type=NotificationMessage.MESSAGE_ERROR,
                        summary_message="The synchronization with the Cisco EoX API was not successful.",
                        detailed_message=msg
                    )

                result = {
                    "error_message": msg
                }

            else:
                # execute all queries from the configuration
                query_eox_records = {}
                failed_queries = []
                failed_query_msgs = {}
                successful_queries = []
                counter = 1

                for query in queries:
                    self.update_state(state=TaskState.PROCESSING, meta={
                        "status_message": "send query <code>%s</code> to the Cisco EoX API (<strong>%d of "
                                          "%d</strong>)..." % (query, counter, len(queries))
                    })

                    # wait some time between the query calls
                    time.sleep(int(app_config.get_cisco_eox_api_sync_wait_time()))
                    try:
                        query_eox_records[query] = cisco_eox_api_crawler.get_raw_api_data(api_query=query)
                        successful_queries.append(query)

                    except CiscoApiCallFailed as ex:
                        msg = "Cisco EoX API call failed (%s)" % str(ex)
                        logger.error("Query %s to Cisco EoX API failed (%s)" % (query, msg), exc_info=True)
                        failed_queries.append(query)
                        failed_query_msgs[query] = str(ex)

                    except Exception as ex:
                        msg = "Unexpected Exception, cannot access the Cisco API. Please ensure that the server is " \
                              "connected to the internet and that the authentication settings are " \
                              "valid."
                        logger.error("Query %s to Cisco EoX API failed (%s)" % (query, msg), exc_info=True)
                        failed_queries.append(query)
                        failed_query_msgs[query] = str(ex)

                    counter += 1

                for key in query_eox_records:
                    amount_of_records = len(query_eox_records[key])
                    self.update_state(state=TaskState.PROCESSING, meta={
                        "status_message": "update database (query <code>%s</code>, processed <b>0</b> of "
                                          "<b>%d</b> results)..." % (key, amount_of_records)
                    })

                    # update database in a separate task
                    update_cisco_eox_records.apply_async(kwargs={
                        "records": query_eox_records[key]
                    })

                # view the queries in the detailed message and all messages (if there are some)
                detailed_message = "The following queries were executed:<br><ul style=\"text-align: left;\">"
                for fq in failed_queries:
                    detailed_message += "<li class=\"text-danger\"><code>%s</code> " \
                                        "(failed, %s)</li>" % (fq, failed_query_msgs.get(fq, "unknown"))
                for sq in successful_queries:
                    detailed_message += "<li><code>%s</code> (<b>affects %d products</b>, " \
                                        "success)</li>" % (sq, len(query_eox_records[sq]))
                detailed_message += "</ul>"

                # show the executed queries in the summary message
                if len(failed_queries) == 0 and len(successful_queries) != 0:
                    summary_html = "The following queries were successful executed: %s" % ", ".join(
                        ["<code>%s</code>" % query for query in successful_queries]
                    )
                    NotificationMessage.objects.create(
                        title=NOTIFICATION_MESSAGE_TITLE, type=NotificationMessage.MESSAGE_SUCCESS,
                        summary_message="The synchronization with the Cisco EoX API was successful. " + summary_html,
                        detailed_message=detailed_message
                    )

                elif len(failed_queries) != 0 and len(successful_queries) == 0:
                    summary_html = "The following queries failed to execute: %s" % ", ".join(
                        ["<code>%s</code>" % query for query in failed_queries]
                    )
                    NotificationMessage.objects.create(
                        title=NOTIFICATION_MESSAGE_TITLE, type=NotificationMessage.MESSAGE_ERROR,
                        summary_message="The synchronization with the Cisco EoX API was not successful. " + summary_html,
                        detailed_message=detailed_message
                    )

                else:
                    summary_html = "The following queries were successful executed: %s\n<br>The following queries " \
                                   "failed to execute: %s" % (
                                       ", ".join(["<code>%s</code>" % query for query in successful_queries]),
                                       ", ".join(["<code>%s</code>" % query for query in failed_queries])
                                   )
                    NotificationMessage.objects.create(
                        title=NOTIFICATION_MESSAGE_TITLE, type=NotificationMessage.MESSAGE_WARNING,
                        summary_message="The synchronization with the Cisco EoX API was partially "
                                        "successful. " + summary_html,
                        detailed_message=detailed_message
                    )

                result = {"status_message": "<p style=\"text-align: left;\">" + detailed_message + "</p>"}

                # if the task was executed eager, set state to SUCCESS (required for testing)
                if self.request.is_eager:
                    self.update_state(state=TaskState.SUCCESS, meta={"status_message": summary_html})

    # remove in progress flag with the cache
    cache.delete("CISCO_EOX_API_SYN_IN_PROGRESS")

    return result
