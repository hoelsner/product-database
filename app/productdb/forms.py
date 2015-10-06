from django import forms
from app.productdb.models import Settings


class CommonSettingsForm(forms.Form):
    cisco_api_enabled = forms.BooleanField(
        initial=False,
        required=False
    )


class CiscoApiSettingsForm(forms.ModelForm):
    cisco_api_client_id = forms.CharField(
        widget=forms.TextInput(attrs={'class': "form-control"})
    )

    cisco_api_client_secret = forms.CharField(
        widget=forms.TextInput(attrs={'class': "form-control"})
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

    class Meta:
        model = Settings
        fields = [
            'cisco_eox_api_auto_sync_auto_create_elements',
            'cisco_eox_api_auto_sync_enabled',
            'cisco_eox_api_auto_sync_queries',
            'eox_api_blacklist',
        ]
