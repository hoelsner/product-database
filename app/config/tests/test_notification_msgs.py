from django.core.urlresolvers import reverse
from django.test import TestCase

from app.config.models import NotificationMessage


class NotificationMessageTest(TestCase):
    """
    Test the Notification Message views
    """

    def test_add_info_message_method(self):
        self.assertTrue(NotificationMessage.objects.all().count() == 0)

        NotificationMessage.add_info_message(
            title="title",
            summary_message="summary message",
            detailed_message="detailed message"
        )

        self.assertTrue(NotificationMessage.objects.filter(type=NotificationMessage.MESSAGE_INFO).count() == 1)
        self.assertIn(
            "title",
            NotificationMessage.objects.filter(type=NotificationMessage.MESSAGE_INFO).first().title
        )

    def test_add_success_message_method(self):
        self.assertTrue(NotificationMessage.objects.all().count() == 0)

        NotificationMessage.add_success_message(
            title="title",
            summary_message="summary message",
            detailed_message="detailed message"
        )

        self.assertTrue(NotificationMessage.objects.filter(type=NotificationMessage.MESSAGE_SUCCESS).count() == 1)
        self.assertIn(
            "title",
            NotificationMessage.objects.filter(type=NotificationMessage.MESSAGE_SUCCESS).first().title
        )

    def test_add_warning_message_method(self):
        self.assertTrue(NotificationMessage.objects.all().count() == 0)

        NotificationMessage.add_warning_message(
            title="title",
            summary_message="summary message",
            detailed_message="detailed message"
        )

        self.assertTrue(NotificationMessage.objects.filter(type=NotificationMessage.MESSAGE_WARNING).count() == 1)
        self.assertIn(
            "title",
            NotificationMessage.objects.filter(type=NotificationMessage.MESSAGE_WARNING).first().title
        )

    def test_add_error_message_method(self):
        self.assertTrue(NotificationMessage.objects.all().count() == 0)

        NotificationMessage.add_error_message(
            title="title",
            summary_message="summary message",
            detailed_message="detailed message"
        )

        self.assertTrue(NotificationMessage.objects.filter(type=NotificationMessage.MESSAGE_ERROR).count() == 1)
        self.assertIn(
            "title",
            NotificationMessage.objects.filter(type=NotificationMessage.MESSAGE_ERROR).first().title
        )

    def test_notifications_not_shown_on_homepage_if_empty(self):
        response = self.client.get(reverse("productdb:home"))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            "recent events",
            response.content.decode("utf-8")
        )

    def test_notifications_shown_on_homepage(self):
        NotificationMessage.objects.create(
            title="mytitle",
            type=NotificationMessage.MESSAGE_ERROR,
            summary_message="summary",
            detailed_message="detailed message"
        )

        self.client.login(username="api", password="api")
        response = self.client.get(reverse("productdb:home"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "recent events",
            response.content.decode("utf-8")
        )
        self.assertIn(
            "mytitle",
            response.content.decode("utf-8")

        )
        self.assertIn(
            "summary",
            response.content.decode("utf-8")

        )
        self.assertNotIn(
            "detailed message",
            response.content.decode("utf-8")
        )

    def test_server_notification_detail_view(self):
        nm = NotificationMessage.objects.create(
            title="mytitle",
            type=NotificationMessage.MESSAGE_ERROR,
            summary_message="summary",
            detailed_message="detailed message"
        )

        response = self.client.get(reverse("productdb_config:notification-detail", kwargs={"message_id": nm.id}))

        self.assertEqual(response.status_code, 200)

        # now the full message is visible
        self.assertIn(
            "mytitle",
            response.content.decode("utf-8")

        )
        self.assertIn(
            "summary",
            response.content.decode("utf-8")

        )
        self.assertIn(
            "detailed message",
            response.content.decode("utf-8")
        )

    def test_server_notification_list_view(self):
        response = self.client.get(reverse("productdb_config:notification-list"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Notification Messages",
            response.content.decode("utf-8")
        )
        self.assertIn(
            "There are currently no notification messages on the server.",
            response.content.decode("utf-8")
        )

        NotificationMessage.objects.create(
            title="mytitle",
            type=NotificationMessage.MESSAGE_ERROR,
            summary_message="summary",
            detailed_message="detailed message"
        )
        response = self.client.get(reverse("productdb_config:notification-list"))

        self.assertEqual(response.status_code, 200)

        # now the full message is visible
        self.assertIn(
            "Notification Messages",
            response.content.decode("utf-8")
        )
        self.assertIn(
            "mytitle",
            response.content.decode("utf-8")

        )
        self.assertIn(
            "summary",
            response.content.decode("utf-8")

        )
        self.assertNotIn(
            "detailed message",
            response.content.decode("utf-8")
        )


