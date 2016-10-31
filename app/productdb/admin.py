from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from reversion_compare.admin import CompareVersionAdmin
from app.productdb.models import Product, Vendor, ProductGroup, ProductList, ProductMigrationOption, \
    ProductMigrationSource
from app.productdb.models import UserProfile
from django.contrib.auth.models import Permission
admin.site.register(Permission)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "user profile"
    verbose_name_plural = 'user profiles'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, )

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class ProductAdmin(CompareVersionAdmin, admin.ModelAdmin):
    list_display = (
        'product_id',
        'description',
        'tags',
        'vendor',
        'current_lifecycle_states',
        'has_migration_options',
        'product_migration_source_names',
        'product_migration_source_names',
        'lc_state_sync',
    )

    search_fields = (
        'product_id',
        'description',
        'tags',
        'vendor__name',
    )

    readonly_fields = (
        'current_lifecycle_states',
        'has_migration_options',
        'preferred_replacement_option',
        'product_migration_source_names',
        'lc_state_sync',
    )

    def has_migration_options(self, obj):
        return obj.has_migration_options()

    def preferred_replacement_option(self, obj):
        result = obj.get_preferred_replacement_option()
        return result.replacement_product_id if result else ""

    def product_migration_source_names(self, obj):
        return "\n".join(obj.get_product_migration_source_names_set())

    def current_lifecycle_states(self, obj):
        val = obj.current_lifecycle_states
        if val:
            return "<br>".join(obj.current_lifecycle_states)
        return ""

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


class ProductMigrationSourceAdmin(CompareVersionAdmin, admin.ModelAdmin):
    list_display = (
        "name",
        "description",
        "preference",
    )

    history_latest_first = True
    ignore_duplicate_revisions = True

admin.site.register(ProductMigrationSource, ProductMigrationSourceAdmin)


class ProductMigrationOptionAdmin(CompareVersionAdmin, admin.ModelAdmin):
    list_display = (
        "product",
        "replacement_product_id",
        "migration_source",
        "comment",
        "migration_product_info_url"
    )

    search_fields = (
        "product__product_id",
        "migration_source__name",
    )

    history_latest_first = True
    ignore_duplicate_revisions = True

admin.site.register(ProductMigrationOption, ProductMigrationOptionAdmin)


class ProductListAdmin(CompareVersionAdmin, admin.ModelAdmin):
    list_display = [
        'name',
        'description',
        'update_user',
        'update_date'
    ]
    fields = [
        'name',
        'description',
        'string_product_list',
        'update_user',
        'update_date'
    ]

    readonly_fields = [
        'update_date'
    ]

    history_latest_first = True
    ignore_duplicate_revisions = True


admin.site.register(ProductList, ProductListAdmin)
