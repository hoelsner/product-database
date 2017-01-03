import logging
from django import forms
from django.contrib.auth.models import AnonymousUser
from django.forms.utils import ErrorList
from rest_framework.authtoken.models import Token
from app.productdb.models import ProductList, UserProfile, Product, ProductMigrationOption, ProductCheck
from app.productdb import utils

logger = logging.getLogger("app.productdb.forms")


class ProductMigrationOptionForm(forms.ModelForm):
    """custom form for the admin page to create or update Product Migration Options"""
    product_id = forms.CharField()
    product = forms.CharField(
        required=False,
        widget=forms.HiddenInput
    )

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList,
                 label_suffix=None, empty_permitted=False, instance=None):
        super().__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, instance)
        if instance:
            self.fields["product_id"].initial = instance.product.product_id

    def clean(self):
        cleaned_data = super(ProductMigrationOptionForm, self).clean()
        product_id = cleaned_data["product_id"]
        replacement_product_id = cleaned_data["replacement_product_id"]

        try:
            product = Product.objects.get(product_id=product_id)
            self.instance.product = product

        except Product.DoesNotExist:
            raise forms.ValidationError({"product_id": "Product not in database, please enter a valid Product ID"})

        if replacement_product_id != self.instance.product.product_id:
            try:
                self.instance.replacement_db_product = Product.objects.get(
                    product_id=self.instance.replacement_product_id
                )

            except Product.DoesNotExist:
                pass

        else:
            raise forms.ValidationError({
                "replacement_product_id": "Product ID that should be replaced cannot be the same as the suggested "
                                          "replacement Product ID"
            })

    class Meta:
        model = ProductMigrationOption
        fields = {
            "product_id",
            "product",
            "replacement_product_id",
            "migration_source",
            "comment",
            "migration_product_info_url",
        }


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(
        label="Contact eMail:",
        help_text="eMail address that is associated to your account"
    )

    regenerate_api_auth_token = forms.BooleanField(
        label="re-create REST API authentication token",
        help_text="re-create the authentication token, only required if you need to invalidate your current token",
        required=False
    )

    def __init__(self, user, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.user = user
        if self.user:
            self.fields["email"].initial = self.user.email

    def save(self, commit=True):
        # drop and recreate the token if the flag is set
        if self.cleaned_data.get("regenerate_api_auth_token", False):
            token, _ = Token.objects.get_or_create(user=self.user)
            token.delete()
            token, _ = Token.objects.get_or_create(user=self.user)
        return super().save(commit)

    class Meta:
        model = UserProfile
        fields = ['preferred_vendor', 'regex_search', 'choose_migration_source']


class ProductListForm(forms.ModelForm):
    class Meta:
        model = ProductList
        fields = ["name", "description", "string_product_list", "version_note"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Name"}),
            "description": forms.Textarea(attrs={"placeholder": "Enter description here"}),
            "string_product_list": forms.Textarea(attrs={"placeholder": "e.g. WS-C2960-24T-S;WS-C2960-48T-S"})
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


class ImportProductMigrationFileUploadForm(forms.Form):
    excel_file = forms.FileField(label="Product Migration Excel File for import:")

    def clean_excel_file(self):
        # validation of the import products excel file
        uploaded_file = self.cleaned_data.get("excel_file")

        if len(uploaded_file.name.split('.')) == 1:
            raise forms.ValidationError("file type not supported.")

        if uploaded_file.name.split('.')[-1] not in ["xlsx"]:
            raise forms.ValidationError("only .xlsx files are allowed")


class ProductCheckForm(forms.ModelForm):
    public_product_check = forms.BooleanField(
        label="public available",
        label_suffix=":",
        help_text="if enabled, everyone can see the Product Check (if not logged in, a Product Check is always "
                  "visible to everyone)",
        required=False,
        initial=False
    )

    is_cisco_show_inventory_output = forms.BooleanField(
        label="input list is Cisco IOS <code>show inventory</code> command(s)",
        help_text="output of one or multiple <code>show inventory</code> commands is used in the product ID list field."
                  " The product IDs are automatically extracted from the command output and any other information are "
                  "withdrawn.",
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()

        # check if the output is provided as show inventory output
        if cleaned_data.get("is_cisco_show_inventory_output", False):
            cleaned_data["input_product_ids"] = "\n".join(utils.parse_cisco_show_inventory(
                cleaned_data["input_product_ids"])
            )

        return cleaned_data

    class Meta:
        model = ProductCheck
        fields = [
            "name",
            "migration_source",
            "input_product_ids",
            "create_user",
        ]
        widgets = {
            "create_user": forms.HiddenInput()
        }
