from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from app.config.models import TextBlock
from app.productdb.models import Product, Vendor, ProductGroup


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


class ProductGroupAdmin(CompareVersionAdmin, admin.ModelAdmin):
    list_display = (
        'name',
        'vendor'
    )

    search_fields = (
        'name',
        'vendor__name'
    )

    history_latest_first = True
    ignore_duplicate_revisions = True

admin.site.register(ProductGroup, ProductGroupAdmin)


class VendorAdmin(CompareVersionAdmin, admin.ModelAdmin):
    fields = (
        'name',
    )

    history_latest_first = True
    ignore_duplicate_revisions = True

admin.site.register(Vendor, VendorAdmin)


class TextBlockAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
    fields = (
        'name',
        'html_content'
    )

admin.site.register(TextBlock, TextBlockAdmin)
