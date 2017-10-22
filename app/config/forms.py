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
        required=False,
        label="<strong>login always required</strong>",
        help_text="This setting enables/disable the public access to the site (except share links). "
    )

    internal_product_id_label = forms.CharField(
        required=False,
        label="Internal Product ID label:",
        help_text="Custom label for the Internal Product ID"
    )

    homepage_text_before = forms.CharField(
        widget=forms.Textarea(attrs={'class': "form-control code"}),
        required=False,
        label="Text before favorite actions:",
        help_text="HTML and/or markdown formatted text"
    )

    homepage_text_after = forms.CharField(
        widget=forms.Textarea(attrs={'class': "form-control code"}),
        required=False,
        label="Text after favorite actions:",
        help_text="HTML and/or markdown formatted text"
    )

    cisco_api_enabled = forms.BooleanField(
        initial=False,
        required=False,
        label="<strong>enable Cisco API</strong>"
    )

    cisco_api_client_id = forms.CharField(
        widget=forms.TextInput(attrs={'class': "form-control"}),
        required=False,
        label="Client ID:",
    )

    cisco_api_client_secret = forms.CharField(
        required=False,
        label="Client Secret:"
    )

    eox_auto_sync_auto_create_elements = forms.BooleanField(
        initial=False,
        required=False,
        label="<strong>auto-create new products</strong>",
        help_text="If enabled, new products are created (if not already existing) if an EoL message is found. "
                  "Otherwise, these entries are ignored."
    )

    eox_api_auto_sync_enabled = forms.BooleanField(
        initial=False,
        required=False,
        label="<strong>periodic synchronization of the Cisco EoX states</strong>",
        help_text="This synchronization tasks utilizes the Cisco EoX API and will automatically update the lifecycle "
                  "state of the products from the configured queries. It is executed by default <strong>on every "
                  "Friday at 3:00 a.m.</strong>."
    )

    eox_api_queries = forms.CharField(
        widget=forms.Textarea(attrs={'class': "form-control"}),
        required=False,
        label="Cisco EoX API queries:",
        help_text="EoX queries are executed line by line. Please note, that every query must contain at least three "
                  "characters. A Wildcard sign (*) is also allowed."
    )

    eox_api_blacklist = forms.CharField(
        widget=forms.Textarea(attrs={'class': "form-control"}),
        required=False,
        label="blacklist for products:",
        help_text="Regular expressions separated by semicolon (;) or word wrap. If a PID matches the regular "
                  "expression, it won't be created in the database. This option is only required, if "
                  "<strong>auto-create new products</strong>-option is enabled."
    )

    eox_api_wait_time = forms.IntegerField(
        min_value=1,
        max_value=60,
        required=False,
        label="Cisco EoX query wait time:",
        help_text="Value between 1 and 60 seconds that is used as a wait timer between the Cisco EoX API queries."
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
