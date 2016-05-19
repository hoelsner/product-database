from django.contrib import admin
from app.productdb.models import Product, Vendor


class ProductAdmin(admin.ModelAdmin):
    fields = (
        'product_id',
        'description',
        'list_price',
        'currency',
        'tags',
        'vendor',
    )

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
        'vendor',
    )

admin.site.register(Product, ProductAdmin)


class VendorAdmin(admin.ModelAdmin):
    fields = (
        'name',
    )

admin.site.register(Vendor, VendorAdmin)
