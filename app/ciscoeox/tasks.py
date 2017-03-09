import logging
import re

import time
from django.core.cache import cache
from django.db import transaction

import app.ciscoeox.api_crawler as cisco_eox_api_crawler
from app.ciscoeox.exception import CredentialsNotFoundException, CiscoApiCallFailed
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
            pl = Product.objects.filter(vendor=cis_vendor)
            for p in pl:
                p.lc_state_sync = False
                p.save()

            # only set the state sync to true if the periodic synchronization is enabled
            if app_config.is_periodic_sync_enabled():
                for query in queries:
                    pl = Product.objects.filter(product_id__regex=query, vendor=cis_vendor)

                    for p in pl:
                        p.lc_state_sync = True
                        p.save()

        return {"status": "Database updated"}

    else:
        return {"error": "No Products associated to \"Cisco Systems\" found in database"}


@app.task(
    serializer='json',
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

        # read queries from configuration
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
            try:
                # test Cisco EoX API access
                success = utils.check_cisco_eox_api_access(
                    app_config.get_cisco_api_client_id(),
                    app_config.get_cisco_api_client_secret(),
                    False
                )

                if not success:
                    msg = "Cannot access the Cisco API. Please ensure that the server is connected to the internet " \
                          "and that the authentication settings are valid."
                    logger.error(msg, exc_info=True)

                    NotificationMessage.objects.create(
                        title=NOTIFICATION_MESSAGE_TITLE,
                        type=NotificationMessage.MESSAGE_ERROR,
                        summary_message=msg,
                        detailed_message="The synchronization with the Cisco EoX API was not started."
                    )

                    result = {
                        "error_message": msg
                    }

                else:
                    # execute all queries from the configuration and collect the results
                    notify_metrics = {
                        "queries": {}
                    }
                    counter = 0
                    for query in queries:
                        self.update_state(state=TaskState.PROCESSING, meta={
                            "status_message": "send query <code>%s</code> to the Cisco EoX API (<strong>%d of "
                                              "%d</strong>)..." % (query, counter + 1, len(queries))
                        })

                        # wait a specific amount of seconds between each update call
                        time.sleep(int(app_config.get_cisco_eox_api_sync_wait_time()))

                        query_results = cisco_eox_api_crawler.update_cisco_eox_database(query)

                        blist_counter = 0
                        update_counter = 0
                        create_counter = 0
                        for qres in query_results:
                            if qres["created"]:
                                create_counter += 1
                            elif qres["updated"]:
                                update_counter += 1
                            elif qres["blacklist"]:
                                blist_counter += 1

                        notify_metrics["queries"][query] = {
                            "amount": len(query_results),
                            "updated_entries": update_counter,
                            "created_entries": create_counter,
                            "blacklisted_entries": blist_counter,
                            "result_details": query_results
                        }

                        counter += 1

                    # create NotificationMessage based on the results
                    detailed_html = ""
                    blist_counter = 0
                    update_counter = 0
                    create_counter = 0
                    for query_key in notify_metrics["queries"].keys():
                        update_counter += notify_metrics["queries"][query_key]["updated_entries"]
                        create_counter += notify_metrics["queries"][query_key]["created_entries"]
                        blist_counter += notify_metrics["queries"][query_key]["blacklisted_entries"]

                        # build detailed string
                        detailed_html += "<div style=\"text-align:left;\"><h3>Query: %s</h3>" % query_key

                        cond_1 = notify_metrics["queries"][query_key]["updated_entries"] == 0
                        cond_1 = cond_1 and (notify_metrics["queries"][query_key]["created_entries"] == 0)
                        cond_1 = cond_1 and (notify_metrics["queries"][query_key]["blacklisted_entries"] == 0)

                        if cond_1:
                            detailed_html += "No changes required."

                        else:
                            detailed_html += "The following products are affected by this update:</p>"
                            detailed_html += "<ul>"

                            for qres in notify_metrics["queries"][query_key]["result_details"]:

                                msg = ""
                                if "message" in qres.keys():
                                    if qres["message"]:
                                        msg = qres["message"]

                                if qres["created"]:
                                    detailed_html += "<li>create the Product <code>%s</code> in the database" % (
                                        qres["PID"]
                                    )
                                    detailed_html += " (%s)</li>" % msg if msg != "" else "</li>"

                                elif qres["updated"]:
                                    detailed_html += "<li>update the Product data for <code>%s</code>" % (
                                        qres["PID"]
                                    )
                                    detailed_html += " (%s)</li>" % msg if msg != "" else "</li>"

                                elif qres["blacklist"]:
                                    detailed_html += "<li>Product data for <code>%s</code> ignored" % (
                                        qres["PID"]
                                    )
                                    detailed_html += " (%s)</li>" % msg if msg != "" else "</li>"

                            detailed_html += "</ul>"

                        detailed_html += "</div>"

                    summary_html = "The synchronization was performed successfully. "

                    if update_counter == 1:
                        summary_html += "<strong>%d</strong> product was updated, " % update_counter
                    else:
                        summary_html += "<strong>%d</strong> products are updated, " % update_counter

                    if create_counter == 1:
                        summary_html += "<strong>%s</strong> product was added to the database and " % create_counter
                    else:
                        summary_html += "<strong>%s</strong> products are added to the database and " % create_counter

                    if blist_counter == 1:
                        summary_html += "<strong>%d</strong> product was ignored." % blist_counter
                    else:
                        summary_html += "<strong>%d</strong> products are ignored." % blist_counter

                    # show the executed queries in the summary message
                    summary_html += " The following queries were executed: %s" % ", ".join(
                        ["<code>%s</code>" % query for query in queries]
                    )

                    NotificationMessage.objects.create(
                        title=NOTIFICATION_MESSAGE_TITLE,
                        type=NotificationMessage.MESSAGE_SUCCESS,
                        summary_message=summary_html,
                        detailed_message=detailed_html
                    )

                    result = {
                        "status_message": detailed_html
                    }

                    # if the task was executed eager, set state to SUCCESS (required for testing)
                    if self.request.is_eager:
                        self.update_state(state=TaskState.SUCCESS, meta={
                            "status_message": detailed_html
                        })

            except CredentialsNotFoundException as ex:
                msg = "Invalid credentials for Cisco EoX API or insufficient access rights (%s)" % str(ex)
                logger.error(msg, exc_info=True)

                NotificationMessage.objects.create(
                    title=NOTIFICATION_MESSAGE_TITLE,
                    type=NotificationMessage.MESSAGE_ERROR,
                    summary_message=msg,
                    detailed_message="The synchronization was performed partially."
                )

                result = {
                    "error_message": msg
                }

            except CiscoApiCallFailed as ex:
                msg = "Cisco EoX API call failed (%s)" % str(ex)
                logger.error(msg, exc_info=True)

                NotificationMessage.objects.create(
                    title=NOTIFICATION_MESSAGE_TITLE,
                    type=NotificationMessage.MESSAGE_ERROR,
                    summary_message=msg,
                    detailed_message="The synchronization was performed partially."
                )

                result = {
                    "error_message": msg
                }
            except Exception as ex:
                msg = "Cannot access the Cisco API. Please ensure that the server is " \
                      "connected to the internet and that the authentication settings are " \
                      "valid."
                logger.error(msg, exc_info=True)

                NotificationMessage.objects.create(
                    title=NOTIFICATION_MESSAGE_TITLE,
                    type=NotificationMessage.MESSAGE_ERROR,
                    summary_message=msg,
                    detailed_message="%s" % str(ex)
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
