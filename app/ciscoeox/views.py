import json
import logging

from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.shortcuts import redirect, render

from app.ciscoeox import tasks
from app.ciscoeox.api_crawler import update_cisco_eox_database
from app.ciscoeox.exception import ConnectionFailedException, CiscoApiCallFailed
from app.config import AppSettings
from django_project.celery import set_meta_data_for_task

logger = logging.getLogger(__name__)


@login_required()
@permission_required('is_superuser', raise_exception=True)
def cisco_eox_query(request):
    """Manual query page against the Cisco EoX Version 5 API (if enabled)

    :param request:
    :return:
    """
    app_config = AppSettings()
    app_config.read_file()

    cisco_api_enabled = app_config.is_cisco_api_enabled()

    context = {
        "is_cisco_api_enabled": cisco_api_enabled
    }

    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        if "sync_cisco_eox_states_now" in request.POST.keys():
            if "sync_cisco_eox_states_query" in request.POST.keys():
                query = request.POST['sync_cisco_eox_states_query']

                if query != "":
                    if len(query.split(" ")) == 1:
                        context['query_executed'] = query
                        try:
                            eox_api_update_records = update_cisco_eox_database(api_query=query)

                        except ConnectionFailedException as ex:
                            eox_api_update_records = ["Cannot contact Cisco API, error message:\n%s" % ex]

                        except CiscoApiCallFailed as ex:
                            eox_api_update_records = [ex]

                        except Exception as ex:
                            logger.debug("execution failed due to unexpected exception", exc_info=True)
                            eox_api_update_records = ["execution failed: %s" % ex]

                        context['eox_api_update_records'] = json.dumps(eox_api_update_records, indent=4, sort_keys=True)

                    else:
                        context['eox_api_update_records'] = "Invalid query '%s': not executed" % \
                                                            request.POST['sync_cisco_eox_states_query']
                else:
                    context['eox_api_update_records'] = ["Please specify a valid query"]

            else:
                context['eox_api_update_records'] = "Query not executed, please select the \"execute it now\" checkbox."

    return render(request, "ciscoeox/cisco_eox_query.html", context=context)


@login_required()
@permission_required('is_superuser', raise_exception=True)
def start_cisco_eox_api_sync_now(request):
    """View that starts an Cisco EoX synchronization and redirects to the given URL
    or the main settings page.

    :param request:
    :return:
    """
    current_id = cache.get("CISCO_EOX_API_SYN_IN_PROGRESS", None)
    if current_id:
        logger.info("task already scheduled, redirect to in-progress dialog (%s)" % current_id)
        return redirect(reverse("task_in_progress", kwargs={"task_id": current_id}))

    task = tasks.execute_task_to_synchronize_cisco_eox_states.delay(ignore_periodic_sync_flag=True)
    set_meta_data_for_task(
        task_id=task.id,
        title="Synchronize local database with Cisco EoX API",
        auto_redirect=False,
        redirect_to=reverse("productdb_config:status")
    )
    cache.set("CISCO_EOX_API_SYN_IN_PROGRESS", task.id, 60*60*3)  # timeout after 3 hours, should not take longer

    return redirect(reverse("task_in_progress", kwargs={"task_id": task.id}))
