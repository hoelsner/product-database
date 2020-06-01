"""
Test suite for the productdb.forms module
"""
import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.authtoken.models import Token
from app.productdb import utils, models
from app.productdb.forms import UserProfileForm, ProductListForm, ImportProductsFileUploadForm, \
    ImportProductMigrationFileUploadForm, ProductMigrationOptionForm, ProductCheckForm
from app.productdb.models import Vendor, UserProfile

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures("import_default_vendors")
class TestUserProfileForm:
    def test_form(self):
        user = User.objects.create(username="foo")
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
        user = User.objects.create(username="foo", email="test@test.com")
        data = {
            "email": user.email,
            "preferred_vendor": 1
        }
        form = UserProfileForm(user, data=data, instance=user.profile)

        assert form.is_valid() is True, form.errors
        assert form.cleaned_data.get("email") == user.email, "User eMail should be added automatically"

    def test_recreate_token(self):
        user = User.objects.create(username="user")
        up = UserProfile.objects.get(user=user)
        data = {
            "email": "a@b.com",
            "preferred_vendor": 1
        }
        # get or create the API authentication token
        token = Token.objects.create(user=user)
        org_key = token.key

        form = UserProfileForm(instance=up, user=user, data=data)
        assert form.is_valid() is True
        form.save()

        token = Token.objects.get(user=user)
        assert token.key == org_key  # key is not changed

        # post with regenerate_api_auth_token parameter
        data.update({
            "regenerate_api_auth_token": "True"
        })
        form = UserProfileForm(instance=up, user=user, data=data)
        assert form.is_valid() is True
        form.save()

        token = Token.objects.get(user=user)
        assert token.key != org_key  # key was changed


@pytest.mark.usefixtures("import_default_vendors")
class TestProductListForm:
    def test_form(self):
        form = ProductListForm(data={})
        v = Vendor.objects.get(id=1)
        assert form.is_valid() is False
        assert "name" in form.errors
        assert "description" not in form.errors, "Null/Blank values are allowed"
        assert "string_product_list" in form.errors

        data = {
            "name": "Test Product List",
            "description": "",
            "string_product_list": "",
            "vendor": "1"
        }
        form = ProductListForm(data=data)
        assert form.is_valid() is False
        assert "name" not in form.errors, "Should be allowed (can be any string)"
        assert "description" not in form.errors, "Null/Blank values are allowed"
        assert "string_product_list" in form.errors, "At least one Product is required"

        data = {
            "name": "Test Product List",
            "description": "",
            "string_product_list": "Product",
            "vendor": "1"
        }
        models.Product.objects.create(product_id="Product", vendor=v)
        form = ProductListForm(data=data)
        assert form.is_valid() is True, form.errors

    @pytest.mark.usefixtures("import_default_vendors")
    def test_input_variations_of_string_product_list(self):
        v = Vendor.objects.get(name__contains="Cisco")
        models.Product.objects.create(product_id="Product A", vendor=v)
        models.Product.objects.create(product_id="Product B", vendor=v)
        models.Product.objects.create(product_id="Product C", vendor=v)
        data = {
            "name": "Test Product List",
            "description": "",
            "string_product_list": "Product A",
            "vendor": "1"
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
        expected_error = "The following products are not found in the database for the vendor Cisco Systems: Product D"
        assert expected_error in str(form.errors["__all__"]), "Should list products that are not found"


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
        authuser = User.objects.create(username="foo")
        files = {"excel_file": SimpleUploadedFile("myfile.xlsx", b"yxz")}
        data = {"suppress_notification": False}
        form = ImportProductsFileUploadForm(user=authuser, data=data, files=files)

        assert form.is_valid() is True
        assert form.fields["suppress_notification"].disabled is True
        assert form.cleaned_data["suppress_notification"] is True

        # superusers are allowed to change the parameter
        superuser = User.objects.create(username="test", is_superuser=True)
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


@pytest.mark.usefixtures("import_default_vendors")
class TestProductMigrationOptionForm:
    def test_form(self):
        p = models.Product.objects.create(product_id="Test", vendor=Vendor.objects.get(id=1))
        mg = migration_source = models.ProductMigrationSource.objects.create(name="Test")

        form = ProductMigrationOptionForm(data={
            "migration_source": migration_source.id,
            "product_id": "some value that is not part of the database",
            "replacement_product_id": "Another Test"
        })
        assert form.is_valid() is False
        assert "product_id" in form.errors
        assert form.errors["product_id"] == ["Product not in database, please enter a valid Product ID"]

        form = ProductMigrationOptionForm(data={
            "migration_source": migration_source.id,
            "product_id": "Test",
            "replacement_product_id": "Test"
        })
        assert form.is_valid() is False
        assert "replacement_product_id" in form.errors
        assert form.errors["replacement_product_id"] == ["Product ID that should be replaced cannot be the same "
                                                         "as the suggested replacement Product ID"]

        form = ProductMigrationOptionForm(data={
            "migration_source": migration_source.id,
            "product_id": "Test",
            "replacement_product_id": "Another Test"
        })
        assert form.is_valid() is True

        pmo = models.ProductMigrationOption.objects.create(product=p, migration_source=mg)
        form = ProductMigrationOptionForm(instance=pmo, data={
            "migration_source": migration_source.id,
            "product_id": "Test",
            "replacement_product_id": "Another Test replacement"
        })
        assert form.is_valid() is True


class TestProductCheckForm:
    def test_form(self, monkeypatch):
        # patch the parse_cisco_show_inventory method
        monkeypatch.setattr(utils, "parse_cisco_show_inventory", lambda content: ["a", "b", "c"])

        form = ProductCheckForm()
        assert form.is_valid() is False

        form = ProductCheckForm(data={
            "name": "test",
            "input_product_ids": "Test",
        })

        assert form.is_valid() is True
        form.save()
        assert form.instance.input_product_ids == "Test"

        form = ProductCheckForm(data={
            "name": "test",
            "input_product_ids": "output of show inventory",
            "is_cisco_show_inventory_output": "True"
        })

        assert form.is_valid() is True
        form.save()
        assert form.instance.input_product_ids == "a\nb\nc"
