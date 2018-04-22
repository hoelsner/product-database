from django.core.management.base import BaseCommand
from django.core.cache import cache
from app.ciscoeox.management.commands import get_task_state_message


class Command(BaseCommand):
    help = "show status of the last initial import task"

    def handle(self, *args, **kwargs):
        task_id = cache.get("CISCO_EOX_INITIAL_SYN_LAST_RUN", None)
        self.stdout.write(get_task_state_message(task_id))
