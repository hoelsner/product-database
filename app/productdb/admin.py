from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from reversion_compare.admin import CompareVersionAdmin
from app.productdb.models import Product, Vendor, ProductGroup, ProductList
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
    )

    search_fields = (
        'product_id',
        'description',
        'tags',
        'vendor__name',
        'current_lifecycle_states',
    )

    readonly_fields = (
        'current_lifecycle_states',
    )

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


class ProductListAdmin(admin.ModelAdmin):
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
