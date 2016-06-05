from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.test import TestCase, override_settings

from app.config import AppSettings


class TestCeleryTaskCreation(TestCase):
    """
    This test verifies that a celery task is created in celery when calling certain URLs with a specific parameter
    """
    fixtures = ['default_vendors.yaml', 'default_users.yaml']

    @override_settings(BROKER_URL='memory://')
    def test_trigger_manual_cisco_eox_synchronization(self):
        """
        Test if a Cisco EoX synchronization task is scheduled after
        :return:
        """
        app_config = AppSettings()
        app_config.read_file()

        app_config.set_cisco_api_enabled(True)
        app_config.set_periodic_sync_enabled(True)
        app_config.write_file()

        # schedule Cisco EoX API update
        url = reverse('cisco_api:start_cisco_eox_api_sync_now')
        self.client.login(username="pdb_admin", password="pdb_admin")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        # verify that task ID is saved in the cache (set by the schedule call)
        task_id = cache.get("CISCO_EOX_API_SYN_IN_PROGRESS", "")
        self.assertNotEqual(task_id, "")

