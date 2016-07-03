from django import forms
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
