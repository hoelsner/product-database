import logging
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse
from django.core.cache import cache
from django.shortcuts import redirect
from app.ciscoeox import tasks
from django_project.celery import set_meta_data_for_task

logger = logging.getLogger("productdb")


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
