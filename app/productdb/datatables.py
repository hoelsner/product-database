from django_datatables_view.base_datatable_view import BaseDatatableView
from app.productdb import utils as app_util
from .models import Product
from django.db.models import Q


class LifecycleListJson(BaseDatatableView):
    # define column names that will be used in sorting
    # order is important and should be same as order of columns
    # displayed by datatables. For non sortable columns use empty
    # value like ''
    order_columns = ['product_id',
                     'end_of_sale_date',
                     'end_of_sw_maintenance_date',
                     'end_of_support_date',
                     'description',
                     'eol_ext_announcement_date',
                     'end_of_routine_failure_analysis',
                     'end_of_service_contract_renewal',
                     'end_of_new_service_attachment_date',
                     'end_of_support_date',
                     'eol_reference_number',
                     'eol_reference_url']
    vendor_id = 0

    def get_initial_queryset(self):
        if self.kwargs['vendor_id']:
            self.vendor_id = self.kwargs['vendor_id']

        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        return Product.objects.filter(vendor__id=self.vendor_id)\
            .filter(Q(eol_ext_announcement_date__isnull=False) |
                    Q(end_of_sale_date__isnull=False))

    def filter_queryset(self, qs):
        # use request parameters to filter queryset
        search_string = self.request.GET.get('search[value]', None)

        if search_string:
            qs = qs.filter(product_id__contains=search_string)

        return qs

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []

        for item in qs:
            result = app_util.normalize_date(item)

            json_data.append(result)
        return json_data


class VendorProductListJson(BaseDatatableView):
    # define column names that will be used in sorting
    # order is important and should be same as order of columns
    # displayed by datatables. For non sortable columns use empty
    # value like ''
    order_columns = ['product_id',
                     'description',
                     'list_price',
                     'currency']
    vendor_id = 0

    def get_initial_queryset(self):
        if self.kwargs['vendor_id']:
            self.vendor_id = self.kwargs['vendor_id']

        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        return Product.objects.filter(vendor__id=self.vendor_id)

    def filter_queryset(self, qs):
        # use request parameters to filter queryset
        search_string = self.request.GET.get('search[value]', None)

        if search_string:
            qs = qs.filter(Q(product_id__contains=search_string)|
                           Q(description__contains=search_string))

        return qs

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []

        for item in qs:
            json_data.append({
                "product_id": item.product_id,
                "description": item.description,
                "list_price": item.list_price,
                "currency": item.currency
            })
        return json_data


class ListProductsJson(BaseDatatableView):
    # define column names that will be used in sorting
    # order is important and should be same as order of columns
    # displayed by datatables. For non sortable columns use empty
    # value like ''
    order_columns = ['vendor',
                     'product_id',
                     'description',
                     'list_price',
                     'currency']
    product_list_id = 0

    def get_initial_queryset(self):
        if self.kwargs['product_list_id']:
            self.product_list_id = self.kwargs['product_list_id']

        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        return Product.objects.filter(lists=self.product_list_id)

    def filter_queryset(self, qs):
        # use request parameters to filter queryset
        search_string = self.request.GET.get('search[value]', None)

        if search_string:
            qs = qs.filter(Q(product_id__contains=search_string)|
                           Q(description__contains=search_string))

        return qs

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []

        for item in qs:
            json_data.append({
                "vendor": item.vendor.name,
                "product_id": item.product_id,
                "description": item.description,
                "list_price": item.list_price,
                "currency": item.currency
            })
        return json_data
