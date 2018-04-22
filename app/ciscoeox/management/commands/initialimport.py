from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from django.utils.timezone import timedelta, now
from app.ciscoeox import tasks
from app.ciscoeox.management.commands import get_task_state_message
from app.config.settings import AppSettings


class Command(BaseCommand):
    help = "initial data import from the Cisco EoX API (if configured)"

    def add_arguments(self, parser):
        parser.add_argument(
            "years",
            help="Years that should be queries for the initial import (e.g. 2018,2017,2016)",
            nargs="+",
            type=int
        )

    def handle(self, *args, **kwargs):
        app_settings = AppSettings()

        if not app_settings.is_cisco_api_enabled():
            raise CommandError("Please configure the Cisco EoX API in the settings prior running this task")

        # check if task is already running, if so print status and continue
        task_id = cache.get("CISCO_EOX_INITIAL_SYN_IN_PROGRESS", None)

        if task_id is None:
            # start initial import
            eta = now() + timedelta(seconds=3)
            task = tasks.initial_sync_with_cisco_eox_api.apply_async(
                eta=eta,
                args=(kwargs["years"], )
            )

            cache.set("CISCO_EOX_INITIAL_SYN_IN_PROGRESS", task.id, 60 * 60 * 48)
            cache.set("CISCO_EOX_INITIAL_SYN_LAST_RUN", task.id, 60 * 60 * 48)

            self.stdout.write("Task successful started...")

        else:
            msg = get_task_state_message(task_id)
            raise CommandError("initial import already running... \n%s" % msg)
