import logging
import re
from django import forms
from django.core.exceptions import ValidationError

from app.config.models import NotificationMessage


class NotificationMessageForm(forms.ModelForm):
    class Meta:
        model = NotificationMessage
        exclude = [
            "created"
        ]


class SettingsForm(forms.Form):
    """
    settings form
    """
    login_only_mode = forms.BooleanField(
        initial=False,
        required=False
    )

    homepage_text_before = forms.CharField(
        widget=forms.Textarea(attrs={'class': "form-control code"}),
        required=False
    )

    homepage_text_after = forms.CharField(
        widget=forms.Textarea(attrs={'class': "form-control code"}),
        required=False
    )

    cisco_api_enabled = forms.BooleanField(
        initial=False,
        required=False
    )

    cisco_api_client_id = forms.CharField(
        widget=forms.TextInput(attrs={'class': "form-control"}),
        required=False
    )

    cisco_api_client_secret = forms.CharField(
        widget=forms.TextInput(attrs={'class': "form-control"}),
        required=False
    )

    eox_auto_sync_auto_create_elements = forms.BooleanField(
        initial=False,
        required=False
    )

    eox_api_auto_sync_enabled = forms.BooleanField(
        initial=False,
        required=False
    )

    eox_api_queries = forms.CharField(
        widget=forms.Textarea(attrs={'class': "form-control"}),
        required=False
    )

    eox_api_blacklist = forms.CharField(
        widget=forms.Textarea(attrs={'class': "form-control"}),
        required=False
    )

    def _get_eox_api_blacklist_as_list(self):
        if "eox_api_blacklist" in self.data:
            values = []
            for line in self.data["eox_api_blacklist"].splitlines():
                values += line.split(";")
            values = sorted([e.strip() for e in values])
            return sorted(list(set(values)))
        return []

    def clean_eox_api_blacklist(self):
        # normalize the format of the entries
        cleaned_values = self._get_eox_api_blacklist_as_list()

        # verify that these are valid regular expressions
        error_entries = []
        for stmt in cleaned_values:
            try:
                re.compile(stmt)

            except:
                logging.error("Invalid regular expression found: %s" % stmt)
                error_entries += [stmt]

        if len(error_entries) != 0 and cleaned_values != 0:
            raise ValidationError("Invalid regular expression found: %s" % "; ".join(error_entries))

        else:
            return "\n".join(cleaned_values)
