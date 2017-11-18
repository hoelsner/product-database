import logging
import re

import time
from django.core.cache import cache
from django.db import transaction
from django.core.exceptions import ValidationError

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

        return {"status": "Database updated"}

    else:
        return {"error": "No Products associated to \"Cisco Systems\" found in database"}


@app.task(
    serializer="json",
    name="ciscoeox.synchronize_with_cisco_eox_api",
    bind=True
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

    if run_task or ignore_periodic_sync_flag:
        logger.info("start sync with Cisco EoX API...")
        self.update_state(state=TaskState.PROCESSING, meta={
            "status_message": "sync with Cisco EoX API..."
        })

        # read configuration for the Cisco EoX API synchronization
        queries = app_config.get_cisco_eox_api_queries_as_list()
        blacklist_raw_string = app_config.get_product_blacklist_regex()
        create_missing = app_config.is_auto_create_new_products()

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

            if test_result:
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
                        query_eox_records[query] = cisco_eox_api_crawler.get_raw_api_data(query)
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

                # build blacklist from configuration
                blacklist = []
                for e in [e.split(";") for e in blacklist_raw_string.splitlines()]:
                    blacklist += e
                blacklist = [e for e in blacklist if e != ""]

                # update data in database
                self.update_state(state=TaskState.PROCESSING, meta={
                    "status_message": "update database..."
                })
                messages = {}
                for key in query_eox_records:
                    amount_of_records = len(query_eox_records[key])
                    self.update_state(state=TaskState.PROCESSING, meta={
                        "status_message": "update database (query <code>%s</code>, processed <b>0</b> of "
                                          "<b>%d</b> results)..." % (key, amount_of_records)
                    })
                    counter = 0
                    for record in query_eox_records[key]:
                        if counter % 100 == 0:
                            self.update_state(state=TaskState.PROCESSING, meta={
                                "status_message": "update database (query <code>%s</code>, processed <b>%d</b> of "
                                                  "<b>%d</b> results)..." % (key, counter, amount_of_records)
                            })

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

                # view the queries in the detailed message and all messages (if there are some)
                detailed_message = "The following queries were executed:<br><ul style=\"text-align: left;\">"
                for fq in failed_queries:
                    detailed_message += "<li class=\"text-danger\"><code>%s</code> " \
                                        "(failed, %s)</li>" % (fq, failed_query_msgs.get(fq, "unknown"))
                for sq in successful_queries:
                    detailed_message += "<li><code>%s</code> (<b>affects %d products</b>, " \
                                        "success)</li>" % (sq, len(query_eox_records[sq]))
                detailed_message += "</ul>"

                if len(messages) > 0:
                    detailed_message += "<br>The following comment/errors occurred " \
                                        "during the synchronization:<br><ul style=\"text-align: left;\">"
                    for e in messages.keys():
                        detailed_message += "<li><code>%s</code>: %s</li>" % (e, messages[e])
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

            else:
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
        result = {
            "status_message": "task not enabled"
        }

    # remove in progress flag with the cache
    cache.delete("CISCO_EOX_API_SYN_IN_PROGRESS")

    return result
