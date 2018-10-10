from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from reversion_compare.admin import CompareVersionAdmin
from app.productdb.forms import ProductMigrationOptionForm
from app.productdb.models import Product, Vendor, ProductGroup, ProductList, ProductMigrationOption, \
    ProductMigrationSource, ProductCheck, ProductCheckEntry
from app.productdb.models import UserProfile
from django.contrib.auth.models import Permission

admin.site.register(Permission)
admin.site.unregister(User)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "user profile"
    verbose_name_plural = "user profiles"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login",
    ]
    inlines = (UserProfileInline, )


@admin.register(Product)
class ProductAdmin(CompareVersionAdmin, admin.ModelAdmin):
    list_display = (
        "product_id",
        "description",
        "vendor",
        "eox_update_time_stamp",
        "end_of_sale_date",
        "end_of_support_date",
        "has_migration_options",
        "product_migration_source_names",
        "lc_state_sync",
    )

    search_fields = (
        "product_id",
        "description",
        "tags",
        "vendor__name",
    )

    readonly_fields = (
        "current_lifecycle_states",
        "has_migration_options",
        "preferred_replacement_option",
        "product_migration_source_names",
        "lc_state_sync",
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


@admin.register(ProductGroup)
class ProductGroupAdmin(CompareVersionAdmin, admin.ModelAdmin):
    list_display = (
        "name",
        "vendor"
    )

    search_fields = (
        "name",
        "vendor__name"
    )

    history_latest_first = True
    ignore_duplicate_revisions = True


@admin.register(Vendor)
class VendorAdmin(CompareVersionAdmin, admin.ModelAdmin):
    fields = (
        "name",
    )

    history_latest_first = True
    ignore_duplicate_revisions = True


@admin.register(ProductMigrationSource)
class ProductMigrationSourceAdmin(CompareVersionAdmin, admin.ModelAdmin):
    list_display = (
        "name",
        "description",
        "preference",
    )

    history_latest_first = True
    ignore_duplicate_revisions = True


@admin.register(ProductMigrationOption)
class ProductMigrationOptionAdmin(CompareVersionAdmin, admin.ModelAdmin):
    form = ProductMigrationOptionForm
    list_display = (
        "product",
        "replacement_product_id",
        "migration_source",
        "comment",
        "migration_product_info_url",
        "is_replacement_in_db"
    )

    fields = [
        "product_id",
        "replacement_product_id",
        "migration_source",
        "comment",
        "migration_product_info_url",
    ]

    readonly_fields = [
        "is_replacement_in_db"
    ]

    search_fields = (
        "product__product_id",
        "migration_source__name",
    )

    history_latest_first = True
    ignore_duplicate_revisions = True


@admin.register(ProductList)
class ProductListAdmin(CompareVersionAdmin, admin.ModelAdmin):
    list_display = [
        "name",
        "description",
        "update_user",
        "update_date"
    ]
    fields = [
        "name",
        "description",
        "string_product_list",
        "version_note",
        "update_user",
        "update_date"
    ]

    readonly_fields = [
        "update_date"
    ]

    history_latest_first = True
    ignore_duplicate_revisions = True


@admin.register(ProductCheck)
class ProductCheckAdmin(CompareVersionAdmin, admin.ModelAdmin):
    list_display = [
        "name",
        "migration_source",
        "last_change",
        "create_user",
        "in_progress",
        "id",
    ]
    fields = [
        "name",
        "migration_source",
        "input_product_ids",
        "last_change",
        "create_user",
        "task_id"
    ]

    readonly_fields = [
        "last_change",
        "in_progress",
        "input_product_ids"
    ]

    history_latest_first = True
    ignore_duplicate_revisions = True


@admin.register(ProductCheckEntry)
class ProductCheckEntryAdmin(CompareVersionAdmin, admin.ModelAdmin):
    list_display = [
        "product_check",
        "input_product_id",
        "product_in_database",
        "in_database",
        "amount",
        "migration_product_id",
    ]
    fields = [
        "product_check",
        "input_product_id",
        "product_in_database",
        "in_database",
        "amount",
        "migration_product_id",
    ]

    readonly_fields = [
        "product_in_database",
        "in_database",
        "migration_product_id",
        "part_of_product_list"
    ]

    history_latest_first = True
    ignore_duplicate_revisions = True
