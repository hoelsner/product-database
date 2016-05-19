from django.core.urlresolvers import reverse
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
        url = reverse('productdb:schedule_cisco_eox_api_sync_now')
        self.client.login(username="admin", password="admin")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        # verify that task ID is saved in settings (set by the schedule call)
        app_config.read_file()
        task_id = app_config.get_string(
            section=AppSettings.CISCO_EOX_CRAWLER_SECTION,
            key="eox_api_sync_task_id"
        )
        self.assertNotEqual(task_id, "")

