from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from app.productdb.models import Product, Vendor


class ProductAdmin(CompareVersionAdmin, admin.ModelAdmin):
    list_display = (
        'product_id',
        'description',
        'tags',
        'vendor',
    )

    search_fields = (
        'product_id',
        'description',
        'tags',
        'vendor__name',
    )

    history_latest_first = True
    ignore_duplicate_revisions = True

admin.site.register(Product, ProductAdmin)


class VendorAdmin(CompareVersionAdmin, admin.ModelAdmin):
    fields = (
        'name',
    )

    history_latest_first = True
    ignore_duplicate_revisions = True

admin.site.register(Vendor, VendorAdmin)
