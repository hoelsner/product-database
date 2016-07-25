import logging
from django.core.cache import cache
import app.ciscoeox.api_crawler as cisco_eox_api_crawler
from app.ciscoeox.exception import CredentialsNotFoundException, CiscoApiCallFailed
from app.config import AppSettings
from app.config.models import NotificationMessage
from app.config.utils import test_cisco_eox_api_access
from django_project.celery import app as app, TaskState

logger = logging.getLogger(__name__)


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
    app_config.read_file()
    run_task = app_config.is_cisco_eox_api_auto_sync_enabled()

    if ignore_periodic_sync_flag:
        run_task = True

    if run_task:
        logger.info("start sync with Cisco EoX API...")
        self.update_state(state=TaskState.PROCESSING, meta={
            "status_message": "sync with Cisco EoX API..."
        })

        # read queries from configuration
        queries_raw_string = app_config.get_cisco_eox_api_queries()

        # clean queries string and remove empty statements
        # (split lines, if any and split the string by semicolon)
        queries = []
        for e in [e.split(";") for e in queries_raw_string.splitlines()]:
            queries += e
        queries = [e for e in queries if e != ""]

        if len(queries) == 0:
            result = {
                "status_message": "No Cisco EoX API queries configured."
            }

        # update the local database with the Cisco EoX API
        else:
            # test Cisco EoX API access
            success, _ = test_cisco_eox_api_access(
                app_config.get_cisco_api_client_id(),
                app_config.get_cisco_api_client_secret(),
                False
            )

            if not success:
                msg = "Cannot access the Cisco API. Please ensure that the server is connected to the internet " \
                      "and that the authentication settings are valid."
                logger.error(msg, exc_info=True)

                NotificationMessage.objects.create(
                    title="Synchronization with Cisco EoX API",
                    type=NotificationMessage.MESSAGE_ERROR,
                    summary_message=msg,
                    detailed_message="The synchronization with the Cisco EoX API was not started."
                )

                result = {
                    "error_message": msg
                }

            else:
                try:
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
                                    if msg != "":
                                        detailed_html += "(%s)</li>" % msg
                                    else:
                                        detailed_html += "</li>"

                                elif qres["updated"]:
                                    detailed_html += "<li>update the Product data for <code>%s</code></li>" % (
                                        qres["PID"]
                                    )
                                    if msg != "":
                                        detailed_html += "(%s)</li>" % msg
                                    else:
                                        detailed_html += "</li>"

                                elif qres["blacklist"]:
                                    detailed_html += "<li>Product data for <code>%s</code> ignored</li>" % (
                                        qres["PID"]
                                    )
                                    if msg != "":
                                        detailed_html += "(%s)</li>" % msg
                                    else:
                                        detailed_html += "</li>"

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
                        title="Synchronization with Cisco EoX API",
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
                        title="Synchronization with Cisco EoX API",
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
                        title="Synchronization with Cisco EoX API",
                        type=NotificationMessage.MESSAGE_ERROR,
                        summary_message=msg,
                        detailed_message="The synchronization was performed partially."
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
