"""
Test suite for the productdb.admin module
"""
import datetime
import pytest
from django.contrib.admin.sites import AdminSite
from app.productdb import models
from app.productdb import admin

pytestmark = pytest.mark.django_db


class TestProductAdmin:
    @pytest.mark.usefixtures("import_default_vendors")
    def test_current_lifecycle_states(self):
        site = AdminSite()
        product_admin = admin.ProductAdmin(models.Product, site)
        obj = models.Product.objects.create(
            product_id="Product",
            eox_update_time_stamp=datetime.datetime.now()
        )

        result = product_admin.current_lifecycle_states(obj)
        expected = "<br>".join(obj.current_lifecycle_states)

        assert result == expected, "should return a HTML representation of the current lifecycle states"

    def test_search_fields(self):
        for fieldname in admin.ProductAdmin.search_fields:
            query = "%s__icontains" % fieldname
            kwargs = {
                query: "reinout"
            }
            print("Test search field: %s" % fieldname)
            site = AdminSite()
            assert admin.ProductAdmin(models.Product, site).model.objects.filter(**kwargs).count() == 0

    @pytest.mark.usefixtures("import_default_vendors")
    def test_current_lifecycle_state_with_none_value(self):
        site = AdminSite()
        product_admin = admin.ProductAdmin(models.Product, site)
        obj = models.Product.objects.create(
            product_id="Product",
            eox_update_time_stamp=None
        )

        result = product_admin.current_lifecycle_states(obj)
        expected = ""

        assert result == expected, "should return a HTML representation of the current lifecycle states"

    @pytest.mark.usefixtures("import_default_vendors")
    def test_has_valid_migration_options(self):
        site = AdminSite()
        product_admin = admin.ProductAdmin(models.Product, site)
        obj = models.Product.objects.create(
            product_id="Product",
            eox_update_time_stamp=None
        )

        result = product_admin.has_migration_options(obj)
        expected = False
        assert result == expected

        models.ProductMigrationOption.objects.create(
            product=obj,
            migration_source=models.ProductMigrationSource.objects.create(name="test")
        )

        result = product_admin.has_migration_options(obj)
        expected = True
        assert result == expected

    @pytest.mark.usefixtures("import_default_vendors")
    def test_preferred_replacement_option(self):
        site = AdminSite()
        product_admin = admin.ProductAdmin(models.Product, site)
        obj = models.Product.objects.create(
            product_id="Product",
            eox_update_time_stamp=None
        )

        result = product_admin.preferred_replacement_option(obj)
        expected = ""
        assert result == expected

        models.ProductMigrationOption.objects.create(
            product=obj,
            migration_source=models.ProductMigrationSource.objects.create(name="test"),
            replacement_product_id="MyProductId"
        )

        result = product_admin.preferred_replacement_option(obj)
        expected = "MyProductId"
        assert result == expected

    @pytest.mark.usefixtures("import_default_vendors")
    def test_product_migration_source_names_set(self):
        site = AdminSite()
        product_admin = admin.ProductAdmin(models.Product, site)
        obj = models.Product.objects.create(
            product_id="Product",
            eox_update_time_stamp=None
        )

        result = product_admin.product_migration_source_names(obj)
        expected = ""
        assert result == expected

        models.ProductMigrationOption.objects.create(
            product=obj,
            migration_source=models.ProductMigrationSource.objects.create(name="test"),
            replacement_product_id="MyProductId"
        )

        result = product_admin.product_migration_source_names(obj)
        expected = "test"
        assert result == expected
        models.ProductMigrationOption.objects.create(
            product=obj,
            migration_source=models.ProductMigrationSource.objects.create(name="test2"),
            replacement_product_id="MyProductId"
        )

        result = product_admin.product_migration_source_names(obj)
        expected = "test\ntest2"
        assert result == expected

