"""
Test suite for the productdb.forms module
"""
import pytest
from django.contrib.auth.models import AnonymousUser, User
from mixer.backend.django import mixer
from django.core.files.uploadedfile import SimpleUploadedFile
from app.productdb.forms import UserProfileForm, ProductListForm, ImportProductsFileUploadForm, \
    ImportProductMigrationFileUploadForm

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures("import_default_vendors")
class TestUserProfileForm:
    def test_form(self):
        user = mixer.blend("auth.User")
        form = UserProfileForm(user, data={})
        assert form.fields["email"].initial == user.email, "Should be the email of the current user"
        assert form.is_valid() is False
        assert "email" in form.errors
        assert "preferred_vendor" in form.errors

        data = {
            "email": "something",
            "preferred_vendor": 1
        }
        form = UserProfileForm(user, data=data)
        assert form.is_valid() is False, "Invalid eMail format, form not valid"
        assert "email" in form.errors, "Should contain field error for the email"
        assert "preferred_vendor" not in form.errors

        data = {
            "email": "a@b.com",
            "preferred_vendor": 1
        }
        form = UserProfileForm(user, data=data)
        assert form.is_valid() is True, form.errors

        data = {
            "email": "a@b.com",
        }
        form = UserProfileForm(user, data=data)
        assert form.is_valid() is False, "Invalid eMail format, form not valid"
        assert "preferred_vendor" in form.errors, "Should contain field error for the preferred_vendor"

    def test_form_with_instance(self):
        user = mixer.blend("auth.User")
        data = {
            "email": user.email,
            "preferred_vendor": 1
        }
        form = UserProfileForm(user, data=data, instance=user.profile)

        assert form.is_valid() is True
        assert form.cleaned_data.get("email") == user.email, "User eMail should be added automatically"


@pytest.mark.usefixtures("import_default_vendors")
class TestProductListForm:
    def test_form(self):
        form = ProductListForm(data={})
        assert form.is_valid() is False
        assert "name" in form.errors
        assert "description" not in form.errors, "Null/Blank values are allowed"
        assert "string_product_list" in form.errors

        data = {
            "name": "Test Product List",
            "description": "",
            "string_product_list": ""
        }
        form = ProductListForm(data=data)
        assert form.is_valid() is False
        assert "name" not in form.errors, "Should be allowed (can be any string)"
        assert "description" not in form.errors, "Null/Blank values are allowed"
        assert "string_product_list" in form.errors, "At least one Product is required"

        data = {
            "name": "Test Product List",
            "description": "",
            "string_product_list": "Product"
        }
        mixer.blend("productdb.Product", product_id="Product")
        form = ProductListForm(data=data)
        assert form.is_valid() is True, form.errors

    def test_input_variations_of_string_product_list(self):
        mixer.blend("productdb.Product", product_id="Product A")
        mixer.blend("productdb.Product", product_id="Product B")
        mixer.blend("productdb.Product", product_id="Product C")
        data = {
            "name": "Test Product List",
            "description": "",
            "string_product_list": "Product A"
        }
        form = ProductListForm(data=data)
        assert form.is_valid() is True, form.errors

        # format with semicolons is allowed
        data["string_product_list"] = "Product A;Product B;Product C"
        form = ProductListForm(data=data)
        assert form.is_valid() is True, form.errors

        # format with line-breaks is allowed
        data["string_product_list"] = "Product A\nProduct B\nProduct C"
        form = ProductListForm(data=data)
        assert form.is_valid() is True, form.errors

        # format with a combination is allowed
        data["string_product_list"] = "Product A\nProduct B;Product C"
        form = ProductListForm(data=data)
        assert form.is_valid() is True, form.errors

        # product IDs are checked during validation, therefore an error is thrown for Product D
        data["string_product_list"] = "Product A\nProduct B;Product D"
        form = ProductListForm(data=data)
        assert form.is_valid() is False, "validation should fail, because Product D doesn't exist"
        assert "string_product_list" in form.errors
        assert "Product D" in str(form.errors["string_product_list"]), "Should list products that are not found"


@pytest.mark.usefixtures("import_default_vendors")
class TestImportProductsFileUploadForm:
    def test_form_suppress_notification_only_for_superusers(self):
        # anonymous users are not allowed to add a notification
        files = {"excel_file": SimpleUploadedFile("myfile.xlsx", b"yxz")}
        data = {"suppress_notification": False}
        form = ImportProductsFileUploadForm(user=AnonymousUser(), data=data, files=files)

        assert form.is_valid() is True
        assert form.fields["suppress_notification"].disabled is True
        assert form.cleaned_data["suppress_notification"] is True

        # authenticated users are not allowed to add a notification
        authuser = mixer.blend("auth.User")
        files = {"excel_file": SimpleUploadedFile("myfile.xlsx", b"yxz")}
        data = {"suppress_notification": False}
        form = ImportProductsFileUploadForm(user=authuser, data=data, files=files)

        assert form.is_valid() is True
        assert form.fields["suppress_notification"].disabled is True
        assert form.cleaned_data["suppress_notification"] is True

        # superusers are allowed to change the parameter
        superuser = mixer.blend("auth.User", is_superuser=True)
        files = {"excel_file": SimpleUploadedFile("myfile.xlsx", b"yxz")}
        data = {"suppress_notification": False}
        form = ImportProductsFileUploadForm(user=superuser, data=data, files=files)

        assert form.is_valid() is True
        assert form.fields["suppress_notification"].disabled is False
        assert form.cleaned_data["suppress_notification"] is False

    def test_form(self):
        form = ImportProductsFileUploadForm(data={}, files={})
        assert form.is_valid() is False
        assert "excel_file" in form.errors
        assert "This field is required." in str(form.errors["excel_file"])

        # verify only the file name, the content will raise an Exception in the further processing
        files = {
            "excel_file": SimpleUploadedFile("myfile", b"yxz")
        }
        form = ImportProductsFileUploadForm(data={}, files=files)
        assert form.is_valid() is False
        assert "excel_file" in form.errors
        assert "file type not supported" in str(form.errors["excel_file"])

        files = {
            "excel_file": SimpleUploadedFile("myfile.png", b"yxz")
        }
        form = ImportProductsFileUploadForm(data={}, files=files)
        assert form.is_valid() is False
        assert "excel_file" in form.errors
        assert "only .xlsx files are allowed" in str(form.errors["excel_file"])

        files = {
            "excel_file": SimpleUploadedFile("myfile.xlsx", b"")
        }
        form = ImportProductsFileUploadForm(data={}, files=files)
        assert form.is_valid() is False
        assert "excel_file" in form.errors
        assert "The submitted file is empty." in str(form.errors["excel_file"])

        files = {
            "excel_file": SimpleUploadedFile("myfile.xlsx", b"yxz")
        }
        form = ImportProductsFileUploadForm(data={}, files=files)
        assert form.is_valid() is True
        assert form.cleaned_data["suppress_notification"] is True, "Should be the True by default"

        files = {
            "excel_file": SimpleUploadedFile("myfile.xlsx", b"yxz")
        }
        data = {
            "suppress_notification": True
        }
        form = ImportProductsFileUploadForm(data=data, files=files)
        assert form.is_valid() is True

        files = {
            "excel_file": SimpleUploadedFile("myfile.xlsx", b"yxz")
        }
        data = {
            "suppress_notification": False
        }
        form = ImportProductsFileUploadForm(data=data, files=files)
        assert form.is_valid() is True

        files = {
            "excel_file": SimpleUploadedFile("myfile.xlsx", b"yxz")
        }
        data = {
            "suppress_notification": True,
            "update_existing_products_only": False
        }
        form = ImportProductsFileUploadForm(data=data, files=files)
        assert form.is_valid() is True

        files = {
            "excel_file": SimpleUploadedFile("myfile.xlsx", b"yxz")
        }
        data = {
            "suppress_notification": True,
            "update_existing_products_only": True
        }
        form = ImportProductsFileUploadForm(data=data, files=files)
        assert form.is_valid() is True


class TestImportProductMigrationFileUploadForm:
    def test_form(self):
        form = ImportProductMigrationFileUploadForm(data={}, files={})
        assert form.is_valid() is False
        assert "excel_file" in form.errors
        assert "This field is required." in str(form.errors["excel_file"])

        # verify only the file name, the content will raise an Exception in the further processing
        files = {
            "excel_file": SimpleUploadedFile("myfile", b"yxz")
        }
        form = ImportProductMigrationFileUploadForm(data={}, files=files)
        assert form.is_valid() is False
        assert "excel_file" in form.errors
        assert "file type not supported" in str(form.errors["excel_file"])

        files = {
            "excel_file": SimpleUploadedFile("myfile.png", b"yxz")
        }
        form = ImportProductMigrationFileUploadForm(data={}, files=files)
        assert form.is_valid() is False
        assert "excel_file" in form.errors
        assert "only .xlsx files are allowed" in str(form.errors["excel_file"])

        files = {
            "excel_file": SimpleUploadedFile("myfile.xlsx", b"")
        }
        form = ImportProductMigrationFileUploadForm(data={}, files=files)
        assert form.is_valid() is False
        assert "excel_file" in form.errors
        assert "The submitted file is empty." in str(form.errors["excel_file"])

        files = {
            "excel_file": SimpleUploadedFile("myfile.xlsx", b"yxz")
        }
        form = ImportProductMigrationFileUploadForm(data={}, files=files)
        assert form.is_valid() is True
