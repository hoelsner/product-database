from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.exceptions import ObjectDoesNotExist
from djcelery.models import PeriodicTask, CrontabSchedule
from app.productdb.models import Settings


CISCO_EOX_API_TASK_NAME = "Cisco EoX API synchronization"


@receiver(post_save, sender=Settings)
def set_cisco_eox_api_synchronization_task_state(instance, **kwargs):
    # reflect the state of the Cisco EoX API to the periodic task
    """
    create the Cisco EoX API synchronization cronjob, that is executed every week at 3 a.m. at Saturday
    :param instance:
    :param kwargs:
    """
    if instance.cisco_api_enabled and instance.cisco_eox_api_auto_sync_enabled:
        # create crontab if required (every week at Saturday at 3 a.m.)
        sched, created = CrontabSchedule.objects.get_or_create(minute="0",
                                                               hour="3",
                                                               day_of_month="*",
                                                               month_of_year="*",
                                                               day_of_week="5",)
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
        # disable eox periodic task
        try:
            PeriodicTask.objects.get(name=CISCO_EOX_API_TASK_NAME).delete()
        except ObjectDoesNotExist:
            pass
