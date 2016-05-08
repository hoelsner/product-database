from django.test import TestCase
from app.productdb.signals import *


class ModelSignalTests(TestCase):
    fixtures = ['default_vendors.yaml']

    def test_create_cisco_eox_sync_task(self):
        s, created = Settings.objects.get_or_create(id=1)
        task_name = CISCO_EOX_API_TASK_NAME

        self.assertFalse(s.cisco_api_enabled)
        self.assertFalse(s.cisco_eox_api_auto_sync_enabled)
        try:
            PeriodicTask.objects.get(name=task_name)
            self.fail("Task not found")
        except ObjectDoesNotExist:
            pass

        s.cisco_api_enabled = True
        s.save()

        self.assertTrue(s.cisco_api_enabled)
        self.assertFalse(s.cisco_eox_api_auto_sync_enabled)
        try:
            PeriodicTask.objects.get(name=task_name)
            self.fail("Task not found")
        except ObjectDoesNotExist:
            pass

        s.cisco_eox_api_auto_sync_enabled = True
        s.save()

        self.assertTrue(s.cisco_api_enabled)
        self.assertTrue(s.cisco_eox_api_auto_sync_enabled)

        obj = PeriodicTask.objects.get(name=task_name)

        self.assertTrue(obj is not None)

        s.cisco_eox_api_auto_sync_enabled = False
        s.save()

        self.assertTrue(s.cisco_api_enabled)
        self.assertFalse(s.cisco_eox_api_auto_sync_enabled)
        try:
            PeriodicTask.objects.get(name=task_name)
            self.fail("Task not found")
        except ObjectDoesNotExist:
            pass

