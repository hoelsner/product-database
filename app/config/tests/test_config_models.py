"""
Test suite for the config.models module
"""
import pytest
from django.core.exceptions import ValidationError
from mixer.backend.django import mixer
from app.config import models
from app.config.models import ConfigOption

pytestmark = pytest.mark.django_db


class TestNotificationMessageModel:
    def test_notification_message(self):
        nm = mixer.blend("config.NotificationMessage")

        assert nm.type == models.NotificationMessage.MESSAGE_INFO, "Should be the default"
        assert str(nm) == nm.title
        assert nm.created is not None
        assert models.NotificationMessage.objects.count() == 1

        nm.type = "CustomTypeThatIsToLong"

        with pytest.raises(ValidationError) as exinfo:
            nm.save()

        assert exinfo.match("type\': \[\"Value \'CustomTypeThatIsToLong\' is not a valid choice.")

        models.NotificationMessage.objects.all().delete()

        assert models.NotificationMessage.objects.count() == 0

        models.NotificationMessage.add_info_message(
            title="My test title",
            summary_message="My summary message",
            detailed_message="My detailed message"
        )

        assert models.NotificationMessage.objects.filter(type=models.NotificationMessage.MESSAGE_INFO).count() == 1
        assert models.NotificationMessage.objects.count() == 1

        models.NotificationMessage.add_error_message(
            title="My test title",
            summary_message="My summary message",
            detailed_message="My detailed message"
        )

        assert models.NotificationMessage.objects.filter(type=models.NotificationMessage.MESSAGE_ERROR).count() == 1
        assert models.NotificationMessage.objects.count() == 2

        models.NotificationMessage.add_success_message(
            title="My test title",
            summary_message="My summary message",
            detailed_message="My detailed message"
        )

        assert models.NotificationMessage.objects.filter(type=models.NotificationMessage.MESSAGE_SUCCESS).count() == 1
        assert models.NotificationMessage.objects.count() == 3

        models.NotificationMessage.add_warning_message(
            title="My test title",
            summary_message="My summary message",
            detailed_message="My detailed message"
        )

        assert models.NotificationMessage.objects.filter(type=models.NotificationMessage.MESSAGE_WARNING).count() == 1
        assert models.NotificationMessage.objects.count() == 4


class TestTextBlockModel:
    def test_model(self):
        tb = mixer.blend("config.TextBlock")
        assert tb.name is not None
        assert tb.html_content is None

    def test_unique_constraint(self):
        tb = mixer.blend("config.TextBlock", name="MyName")
        assert tb.name is not None
        assert tb.html_content is None

        tb.name = "".join("a" for _ in range(0, 513))

        with pytest.raises(ValidationError) as exinfo:
            tb.save()

        assert exinfo.match("name\': \[\'Ensure this value has at most 512 characters \(it has 513\)\.")

        with pytest.raises(ValidationError) as exinfo:
            mixer.blend("config.TextBlock", name="MyName")

        assert exinfo.match("name\': \[\'Text block with this Name already exists.")


class TestConfigOptionModel:
    def test_model(self):
        co = mixer.blend("config.ConfigOption")
        assert co.key is not None
        assert co.value is None

        co = ConfigOption.objects.create(key="test", value="test")
        assert co.key is not None
        assert co.value is not None
        assert str(co) == "test", "Should be the key value"

        # test unique constraint
        with pytest.raises(ValidationError) as exinfo:
            ConfigOption.objects.create(key="test")

        assert exinfo.match("key': \['Config option with this Key already exists")
