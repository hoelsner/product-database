"""
Test suite for the productdb.admin module
"""
import datetime
import pytest
from django.contrib.admin.sites import AdminSite
from mixer.backend.django import mixer
from app.productdb import models
from app.productdb import admin

pytestmark = pytest.mark.django_db


class TestProductAdmin:
    @pytest.mark.usefixtures("import_default_vendors")
    def test_current_lifecycle_states(self):
        site = AdminSite()
        product_admin = admin.ProductAdmin(models.Product, site)
        obj = mixer.blend(
            "productdb.Product",
            name="Product",
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
        obj = mixer.blend(
            "productdb.Product",
            name="Product",
            eox_update_time_stamp=None
        )

        result = product_admin.current_lifecycle_states(obj)
        expected = ""

        assert result == expected, "should return a HTML representation of the current lifecycle states"
