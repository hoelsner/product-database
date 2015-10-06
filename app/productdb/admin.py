from django.contrib import admin
from app.productdb.models import Product, ProductList, Vendor, Settings


class ProductListAdmin(admin.ModelAdmin):
    fields = (
        'product_list_name',
        'products',
    )

admin.site.register(ProductList, ProductListAdmin)


class ProductAdmin(admin.ModelAdmin):
    fields = (
        'product_id',
        'description',
        'list_price',
        'currency',
        'tags',
        # JSON Meta Field cannot be edited
        'lists',
    )

admin.site.register(Product, ProductAdmin)


class VendorAdmin(admin.ModelAdmin):
    fields = (
        'name',
    )

admin.site.register(Vendor, VendorAdmin)


class SettingsAdmin(admin.ModelAdmin):
    fields = (
        'cisco_api_enabled',
        'cisco_eox_api_auto_sync_enabled',
        'cisco_eox_api_auto_sync_auto_create_elements',
        'cisco_eox_api_auto_sync_queries',
        'eox_api_blacklist',
        'cisco_api_credentials_successful_tested',
        'cisco_api_credentials_last_message',
        'cisco_eox_api_auto_sync_last_execution_time',
        'cisco_eox_api_auto_sync_last_execution_result',
        'eox_api_sync_task_id',
        'demo_mode',
    )

admin.site.register(Settings, SettingsAdmin)
