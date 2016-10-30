from django.core.exceptions import ObjectDoesNotExist
from django_datatables_view.base_datatable_view import BaseDatatableView
from .models import Product, ProductGroup
from django.db.models import Q
from app.productdb.utils import is_valid_regex


def get_try_regex_from_user_profile(request):
    if request.user.is_authenticated():
        return request.user.profile.regex_search

    else:
        # default value, if not authenticated
        return False


class ColumnSearchMixin:
    """
    column search implementation for datatables
    """
    # the following dictionary is required in the class, that implements the column based search function
    column_based_filter = {}

    def apply_column_based_search(self, request, query_set, try_regex=True):
        """
        apply the column based search parameters from datatables to the query_set

        :param request: the request object
        :param query_set: the query_set that should be used to apply the filters
        :param try_regex: indicates that the search term should try regular expression first
        """
        # apply column based search parameters
        for name, param in self.column_based_filter.items():
            get_param = 'columns[' + str(param["order"]) + '][search][value]'
            column_search_string = request.GET.get(get_param, None)

            if column_search_string:
                query_set = query_set.filter(**{
                    "%s__%s" % (
                        param["expr"],
                        "iregex" if is_valid_regex(column_search_string) and try_regex else "icontains"
                    ): column_search_string
                })
        return query_set


class VendorProductListJson(BaseDatatableView, ColumnSearchMixin):
    order_columns = [
        'product_id',
        'product_group',
        'description',
        'list_price',
        'tags'
    ]

    column_based_filter = {  # parameters that are required for the column based filtering
        "product_id": {
            "order": 0,
            "expr": "product_id",
        },
        "product_group": {
            "order": 1,
            "expr": "product_group__name",
        },
        "description": {
            "order": 2,
            "expr": "description",
        }
        ,
        "list_price": {
            "order": 3,
            "expr": "list_price",
        },
        "tags": {
            "order": 4,
            "expr": "tags",
        }

    }

    # if no vendor is given, we use the "unassigned" vendor
    vendor_id = 0

    def get_initial_queryset(self):
        if "vendor_id" in self.kwargs:
            if self.kwargs['vendor_id']:
                self.vendor_id = self.kwargs['vendor_id']
        return Product.objects.filter(vendor__id=self.vendor_id).prefetch_related("vendor", "product_group")

    def filter_queryset(self, qs):
        search_string = self.request.GET.get('search[value]', None)
        try_regex = get_try_regex_from_user_profile(self.request)

        if search_string:
            # search in the Product Group name and Vendor name by default
            operation = "iregex" if is_valid_regex(search_string) and try_regex else "icontains"
            qs = qs.filter(
                Q(**{"product_id__%s" % operation: search_string}) |
                Q(**{"description__%s" % operation: search_string})
            )

        # apply column based search
        qs = self.apply_column_based_search(request=self.request, query_set=qs, try_regex=try_regex)

        return qs

    def prepare_results(self, qs):
        json_data = []

        for item in qs:
            product_group_id = ""
            product_group_name = ""
            try:
                if item.product_group:
                    product_group_id = item.product_group.id
                    product_group_name = item.product_group.name

            except ObjectDoesNotExist:
                pass

            json_data.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_group": product_group_name,
                "product_group_id": product_group_id,
                "description": item.description,
                "list_price": item.list_price,
                "currency": item.currency,
                "tags": item.tags,
                "lifecycle_state": item.current_lifecycle_states,
                "eox_update_time_stamp": item.eox_update_time_stamp,
                "eol_ext_announcement_date": item.eol_ext_announcement_date,
                "end_of_sale_date": item.end_of_sale_date,
                "end_of_new_service_attachment_date": item.end_of_new_service_attachment_date,
                "end_of_sw_maintenance_date": item.end_of_sw_maintenance_date,
                "end_of_routine_failure_analysis": item.end_of_routine_failure_analysis,
                "end_of_service_contract_renewal": item.end_of_service_contract_renewal,
                "end_of_sec_vuln_supp_date": item.end_of_sec_vuln_supp_date,
                "end_of_support_date": item.end_of_support_date,
                "eol_reference_number": item.eol_reference_number,
                "eol_reference_url": item.eol_reference_url,
                "lc_state_sync": item.lc_state_sync,
                "internal_product_id": item.internal_product_id
            })
        return json_data


class ListProductGroupsJson(BaseDatatableView, ColumnSearchMixin):
    """
    Product Group datatable endpoint
    """
    order_columns = [
        "vendor",
        "name"
    ]
    column_based_filter = {  # parameters that are required for the column based filtering
        "vendor": {
            "order": 0,
            "expr": "vendor__name",
        },
        "name": {
            "order": 1,
            "expr": "name",
        }
    }

    def get_initial_queryset(self):
        return ProductGroup.objects.all().prefetch_related("vendor")

    def filter_queryset(self, qs):
        # use request parameters to filter queryset
        search_string = self.request.GET.get('search[value]', None)
        try_regex = get_try_regex_from_user_profile(self.request)

        if search_string:
            # search in the Product Group name and Vendor name by default
            operation = "iregex" if is_valid_regex(search_string) and try_regex else "icontains"
            qs = qs.filter(
                Q(**{"name__%s" % operation: search_string}) |
                Q(**{"vendor__name__%s" % operation: search_string})
            )

        # apply column based search
        qs = self.apply_column_based_search(request=self.request, query_set=qs, try_regex=try_regex)

        return qs

    def prepare_results(self, qs):
        json_data = []

        for item in qs:
            json_data.append({
                "id": item.id,
                "vendor": item.vendor.name,
                "name": item.name,
            })

        return json_data


class ListProductsByGroupJson(BaseDatatableView, ColumnSearchMixin):
    """
    Product datatables endpoint for a a specific Product Group
    """
    order_columns = [
        'product_id',
        'description',
        'list_price',
        'tags'
    ]
    column_based_filter = {  # parameters that are required for the column based filtering
        "product_id": {
            "order": 0,
            "expr": "product_id"
        },
        "description": {
            "order": 1,
            "expr": "description"
        },
        "list_price": {
            "order": 2,
            "expr": "list_price"
        },
        "tags": {
            "order": 3,
            "expr": "tags"
        },
    }

    # used if only products from a specific product ID should be shown
    product_group_id = None

    def get_initial_queryset(self):
        self.product_group_id = self.kwargs.get('product_group_id', 0)
        return Product.objects.filter(product_group__id=self.product_group_id)

    def filter_queryset(self, qs):
        # use request parameters to filter queryset
        search_string = self.request.GET.get('search[value]', None)
        try_regex = get_try_regex_from_user_profile(self.request)

        if search_string:
            # search in the Product Group name and Vendor name by default
            operation = "iregex" if is_valid_regex(search_string) and try_regex else "icontains"
            qs = qs.filter(
                Q(**{"product_id__%s" % operation: search_string}) |
                Q(**{"description__%s" % operation: search_string})
            )

        # apply column based search
        qs = self.apply_column_based_search(request=self.request, query_set=qs, try_regex=try_regex)

        return qs

    def prepare_results(self, qs):
        json_data = []

        for item in qs:
            json_data.append({
                "id": item.id,
                "product_id": item.product_id,
                "description": item.description,
                "list_price": item.list_price,
                "currency": item.currency,
                "tags": item.tags,
                "lifecycle_state": item.current_lifecycle_states,
                "eox_update_time_stamp": item.eox_update_time_stamp,
                "eol_ext_announcement_date": item.eol_ext_announcement_date,
                "end_of_sale_date": item.end_of_sale_date,
                "end_of_new_service_attachment_date": item.end_of_new_service_attachment_date,
                "end_of_sw_maintenance_date": item.end_of_sw_maintenance_date,
                "end_of_routine_failure_analysis": item.end_of_routine_failure_analysis,
                "end_of_service_contract_renewal": item.end_of_service_contract_renewal,
                "end_of_sec_vuln_supp_date": item.end_of_sec_vuln_supp_date,
                "end_of_support_date": item.end_of_support_date,
                "eol_reference_number": item.eol_reference_number,
                "eol_reference_url": item.eol_reference_url,
                "lc_state_sync": item.lc_state_sync,
                "internal_product_id": item.internal_product_id
            })
        return json_data


class ListProductsJson(BaseDatatableView, ColumnSearchMixin):
    order_columns = [
        'vendor',
        'product_id',
        'product_group',
        'description',
        'list_price',
        'tags'
    ]
    column_based_filter = {  # parameters that are required for the column based filtering
        "vendor": {
            "order": 0,
            "expr": "vendor__name"
        },
        "product_id": {
            "order": 1,
            "expr": "product_id"
        },
        "product_group": {
            "order": 2,
            "expr": "product_group__name"
        },
        "description": {
            "order": 3,
            "expr": "description"
        },
        "list_price": {
            "order": 4,
            "expr": "list_price"
        },
        "tags": {
            "order": 5,
            "expr": "tags"
        }
    }

    def get_initial_queryset(self):
        return Product.objects.all().prefetch_related("vendor", "product_group")

    def filter_queryset(self, qs):
        # use request parameters to filter queryset
        search_string = self.request.GET.get('search[value]', None)
        try_regex = get_try_regex_from_user_profile(self.request)

        if search_string:
            # search in the Product Group name and Vendor name by default
            operation = "iregex" if is_valid_regex(search_string) and try_regex else "icontains"
            qs = qs.filter(
                Q(**{"product_id__%s" % operation: search_string}) |
                Q(**{"description__%s" % operation: search_string})
            )

        # apply column based search
        qs = self.apply_column_based_search(request=self.request, query_set=qs, try_regex=try_regex)

        return qs

    def prepare_results(self, qs):
        json_data = []

        for item in qs:
            product_group_id = ""
            product_group_name = ""
            try:
                if item.product_group:
                    product_group_id = item.product_group.id
                    product_group_name = item.product_group.name

            except ObjectDoesNotExist:
                pass

            vendor_name = ""
            try:
                if item.vendor:
                    vendor_name = item.vendor.name

            except ObjectDoesNotExist:
                pass

            json_data.append({
                "id": item.id,
                "vendor": vendor_name,
                "product_id": item.product_id,
                "product_group": product_group_name,
                "product_group_id": product_group_id,
                "description": item.description,
                "list_price": item.list_price,
                "currency": item.currency,
                "tags": item.tags,
                "lifecycle_state": item.current_lifecycle_states,
                "eox_update_time_stamp": item.eox_update_time_stamp,
                "eol_ext_announcement_date": item.eol_ext_announcement_date,
                "end_of_sale_date": item.end_of_sale_date,
                "end_of_new_service_attachment_date": item.end_of_new_service_attachment_date,
                "end_of_sw_maintenance_date": item.end_of_sw_maintenance_date,
                "end_of_routine_failure_analysis": item.end_of_routine_failure_analysis,
                "end_of_service_contract_renewal": item.end_of_service_contract_renewal,
                "end_of_sec_vuln_supp_date": item.end_of_sec_vuln_supp_date,
                "end_of_support_date": item.end_of_support_date,
                "eol_reference_number": item.eol_reference_number,
                "eol_reference_url": item.eol_reference_url,
                "lc_state_sync": item.lc_state_sync,
                "internal_product_id": item.internal_product_id
            })
        return json_data
