"""
Test suite for the config.forms module
"""
from app.config.forms import NotificationMessageForm, SettingsForm
from app.config.models import NotificationMessage


class TestNotificationMessageForm:
    def test_form(self):
        form = NotificationMessageForm(data={})
        assert form.is_valid() is False
        assert "summary_message" in form.errors
        assert "title" in form.errors
        assert "type" in form.errors
        assert "detailed_message" in form.errors

        data ={
            "title": "Test title",
            "summary_message": "Test summary message",
            "detailed_message": "Test detailed message",
            "type": NotificationMessage.MESSAGE_INFO
        }
        form = NotificationMessageForm(data=data)
        assert form.is_valid() is True


class TestSettingsForm:
    def test_form(self):
        form = SettingsForm(data={})
        assert form.is_valid() is True

        # test default values
        assert form.cleaned_data["login_only_mode"] is False
        assert form.cleaned_data["homepage_text_before"] is ""
        assert form.cleaned_data["homepage_text_after"] is ""
        assert form.cleaned_data["cisco_api_enabled"] is False
        assert form.cleaned_data["internal_product_id_label"] is ""
        assert form.cleaned_data["eox_auto_sync_auto_create_elements"] is False
        assert form.cleaned_data["eox_api_auto_sync_enabled"] is False

        data = {
            "homepage_text_before": "My text before",
            "homepage_text_after": "My text after"
        }
        form = SettingsForm(data=data)
        assert form.is_valid() is True

        test_internal_product_id = "number"
        data = {
            "internal_product_id_label": test_internal_product_id
        }
        form = SettingsForm(data=data)
        assert form.is_valid() is True
        assert form.cleaned_data["internal_product_id_label"] == test_internal_product_id

    def test_form_cisco_eox_api_wait_time(self):
        # test with only a single invalid entry
        data = {
            "eox_api_wait_time": "Test"
        }
        form = SettingsForm(data=data)
        assert form.is_valid() is False
        assert "eox_api_wait_time" in form.errors
        assert "Enter a whole number." in form.errors["eox_api_wait_time"]

        data = {
            "eox_api_wait_time": "90"
        }
        form = SettingsForm(data=data)
        assert form.is_valid() is False
        assert "eox_api_wait_time" in form.errors
        assert "Ensure this value is less than or equal to 60." in form.errors["eox_api_wait_time"]

        data = {
            "eox_api_wait_time": "-20"
        }
        form = SettingsForm(data=data)
        assert form.is_valid() is False
        assert "eox_api_wait_time" in form.errors
        assert "Ensure this value is greater than or equal to 1." in form.errors["eox_api_wait_time"]

        # test with valid entry
        data = {
            "eox_api_wait_time": "15"
        }
        form = SettingsForm(data=data)
        assert form.is_valid() is True
        assert form.cleaned_data["eox_api_wait_time"] == 15

    def test_form_api_blacklist_entries(self):
        # test with only a single invalid entry
        data = {
            "eox_api_blacklist": "*-RF$"  # invalid regex entry
        }
        form = SettingsForm(data=data)
        assert form.is_valid() is False
        assert "eox_api_blacklist" in form.errors
        assert "Invalid regular expression found: *-RF$" in form.errors["eox_api_blacklist"]

        # test with a valid and an invalid entry, separated by semicolon
        data = {
            "eox_api_blacklist": "^WS-C.*$;*-RF$"
        }
        form = SettingsForm(data=data)
        assert form.is_valid() is False
        assert "eox_api_blacklist" in form.errors
        assert "Invalid regular expression found: *-RF$" in form.errors["eox_api_blacklist"]

        # test with valid and invalid entry, separated by word wrap
        data = {
            "eox_api_blacklist": "*-RF$\n^WS-C.*$"
        }
        form = SettingsForm(data=data)
        assert form.is_valid() is False
        assert "eox_api_blacklist" in form.errors
        assert "Invalid regular expression found: *-RF$" in form.errors["eox_api_blacklist"]

        # test with valid entries separated by semicolon
        data = {
            "eox_api_blacklist": ".*-RF$;^WS-C.*$"
        }
        form = SettingsForm(data=data)
        assert form.is_valid() is True
        assert form.cleaned_data["eox_api_blacklist"] == ".*-RF$\n^WS-C.*$"

        # test with valid entries separated by word wrap
        data = {
            "eox_api_blacklist": ".*-RF$\n^WS-C.*$"
        }
        form = SettingsForm(data=data)
        assert form.is_valid() is True
        assert form.cleaned_data["eox_api_blacklist"] == ".*-RF$\n^WS-C.*$"

        # test with specific Product ID's
        data = {
            "eox_api_blacklist": "WS-C2960-24-S-WS;WS-C2960-24-S-RF"
        }
        form = SettingsForm(data=data)
        assert form.is_valid() is True
        assert form.cleaned_data["eox_api_blacklist"] == "WS-C2960-24-S-RF\nWS-C2960-24-S-WS"
