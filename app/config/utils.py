from django.core.exceptions import ObjectDoesNotExist
from djcelery.models import PeriodicTask, CrontabSchedule
from app.ciscoeox.base_api import CiscoHelloApi, CiscoEoxApi

CISCO_EOX_API_TASK_NAME = "Cisco EoX API crawler"


def test_cisco_hello_api_access(client_id, client_secret, drop_credentials=True):
    """
    test the Cisco API access using the Hello API
    """
    try:
        base_api = CiscoHelloApi()
        base_api.load_client_credentials()

        if drop_credentials:
            base_api.drop_cached_token()

        base_api.client_id = client_id
        base_api.client_secret = client_secret

        base_api.hello_api_call()

        return True

    except:
        return False


def test_cisco_eox_api_access(client_id, client_secret, drop_credentials=True):
    """
    test the Cisco EoX API access
    """
    try:
        base_api = CiscoEoxApi()
        base_api.load_client_credentials()

        if drop_credentials:
            base_api.drop_cached_token()

        base_api.client_id = client_id
        base_api.client_secret = client_secret

        base_api.query_product("WS-C2960-24T")

        return True

    except:
        return False


def update_periodic_cisco_eox_api_crawler_task(
    enabled=True,
    minute="0",
    hour="3",
    day_of_month="*",
    month_of_year="*",
    day_of_week="5"
):
    """
    create the Cisco EoX API crawler cronjob, that is executed every week
    """
    if enabled:
        # create crontab if required (every week at Saturday at 3 a.m.)
        sched, created = CrontabSchedule.objects.get_or_create(
            minute=minute,
            hour=hour,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
            day_of_week=day_of_week
        )
        if created:
            sched.save()

        # create synchronization task if required
        o, created = PeriodicTask.objects.get_or_create(
            name=CISCO_EOX_API_TASK_NAME,
            task="synchronize_with_cisco_eox_api",
            crontab=sched,
        )
        if created:
            o.save()

    else:
        # remove eox periodic task if it exists
        try:
            PeriodicTask.objects.get(name=CISCO_EOX_API_TASK_NAME).delete()

        except ObjectDoesNotExist:
            pass
