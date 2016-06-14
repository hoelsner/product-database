from django.core.urlresolvers import reverse

from tests.base.django_test_cases import DestructiveProductDbFunctionalTest
from django.test import override_settings


@override_settings(DEMO_MODE=True)
class SettingsPermissionTest(DestructiveProductDbFunctionalTest):
    fixtures = ['default_vendors.yaml']

    def test_regular_user_has_no_access_to_settings_pages(self):
        # a user hits the settings page
        self.browser.get(self.server_url + reverse("productdb_config:change_settings"))
        self.browser.implicitly_wait(3)

        # perform login using the regular API user
        # the user will be logged in but is again redirected to the login dialog because of missing permissions
        self.handle_login_dialog(self.API_USERNAME, self.API_PASSWORD, "HTTP 403 - forbidden request")

        # logout user
        self.browser.get(self.server_url + "/productdb/logout/")

    def test_regular_user_has_no_access_to_task_settings_pages(self):
        # a user hits the Manual Cisco EoX synchronization page
        self.browser.get(self.server_url + reverse("cisco_api:eox_query"))
        self.browser.implicitly_wait(3)

        # perform login using the regular API user
        # the user will be logged in but is again redirected to the login dialog because of missing permissions
        self.handle_login_dialog(self.API_USERNAME, self.API_PASSWORD, "HTTP 403 - forbidden request")

        # logout user
        self.browser.get(self.server_url + "/productdb/logout/")

    def test_regular_user_has_no_access_to_the_add_notification_settings(self):
        # a user hits the add notification message page
        self.browser.get(self.server_url + reverse("productdb_config:notification-add"))
        self.browser.implicitly_wait(3)

        # perform login using the regular API user
        # the user will be logged in but is again redirected to the login dialog because of missing permissions
        self.handle_login_dialog(self.API_USERNAME, self.API_PASSWORD, "HTTP 403 - forbidden request")

        # logout user
        self.browser.get(self.server_url + "/productdb/logout/")
