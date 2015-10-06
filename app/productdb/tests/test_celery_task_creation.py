from django.core.urlresolvers import reverse
from django.test import TestCase
from app.productdb.models import Settings


class TestCeleryTaskCreation(TestCase):
    """
    This test verifies that a celery task is created in celery when calling certain URLs with a specific parameter
    """
    fixtures = ['default_vendors.yaml', 'default_users.yaml']

    def test_trigger_manual_cisco_eox_synchronization(self):
        """
        Test if the manual Cisco EoX synchronization can be scheduled manually
        :return:
        """
        print("--> remember to start a redis server when executing this test")
        s, created = Settings.objects.get_or_create(id=0)
        s.cisco_api_enabled = True
        s.cisco_eox_api_auto_sync_enabled = True
        s.save()

        # schedule Cisco EoX API update
        url = reverse('productdb:schedule_cisco_eox_api_sync_now')
        self.client.login(username="admin", password="admin")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        # verify that task ID is saved in settings (set by the schedule call)
        s = Settings.objects.get(id=0)
        self.assertNotEqual(s.eox_api_sync_task_id, "")

