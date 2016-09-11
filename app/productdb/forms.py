import logging
from django import forms
from django.contrib.auth.models import AnonymousUser
from app.productdb.models import ProductList, UserProfile

logger = logging.getLogger("app.productdb.forms")


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(
        label="Contact eMail:",
        help_text="eMail address that is associated to your account"
    )

    def __init__(self, user, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.user = user
        if self.user:
            self.fields["email"].initial = self.user.email

    class Meta:
        model = UserProfile
        fields = ['preferred_vendor', 'regex_search']


class ProductListForm(forms.ModelForm):
    class Meta:
        model = ProductList
        fields = ['name', 'description', 'string_product_list']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Name'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter description here'}),
            'string_product_list': forms.Textarea(attrs={'placeholder': 'e.g. WS-C2960-24T-S;WS-C2960-48T-S'})
        }


class ImportProductsFileUploadForm(forms.Form):
    FILE_EXT_WHITELIST = [
        "xlsx",
    ]

    excel_file = forms.FileField(
        label="Upload Excel File:"
    )

    suppress_notification = forms.BooleanField(
        required=False,
        label="Suppress Server Notification Message"
    )

    update_existing_products_only = forms.BooleanField(
        required=False,
        label="Update only existing Products",
        help_text="Use this option if you need to update the existing Products in the database (e.g. update the prices "
                  "based on a price list)"
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.user = user
        else:
            self.user = AnonymousUser()

        if not self.user.is_superuser:
            # disable the suppress_notification option if the user is not the superuser
            self.fields["suppress_notification"].disabled = True

        self.fields["suppress_notification"].initial = True

    def clean_excel_file(self):
        # validation of the import products excel file
        uploaded_file = self.cleaned_data.get("excel_file")

        if len(uploaded_file.name.split('.')) == 1:
            raise forms.ValidationError("file type not supported.")

        if uploaded_file.name.split('.')[-1] not in self.FILE_EXT_WHITELIST:
            raise forms.ValidationError("only .xlsx files are allowed")
