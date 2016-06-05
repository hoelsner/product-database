from django_datatables_view.base_datatable_view import BaseDatatableView
from .models import Product
from django.db.models import Q


class VendorProductListJson(BaseDatatableView):
    # define column names that will be used in sorting
    # order is important and should be same as order of columns
    # displayed by datatables. For non sortable columns use empty
    # value like ''
    order_columns = [
        'product_id',
        'description',
        'list_price',
        'tags'
    ]
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
            qs = qs.filter(Q(product_id__contains=search_string) |
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
                "eol_reference_url": item.eol_reference_url
            })
        return json_data


class ListProductsJson(BaseDatatableView):
    # define column names that will be used in sorting
    # order is important and should be same as order of columns
    # displayed by datatables. For non sortable columns use empty
    # value like ''
    order_columns = [
        'vendor',
        'product_id',
        'description',
        'list_price',
        'tags'
    ]

    def get_initial_queryset(self):
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        return Product.objects.all()

    def filter_queryset(self, qs):
        # use request parameters to filter queryset
        search_string = self.request.GET.get('search[value]', None)

        if search_string:
            qs = qs.filter(Q(product_id__contains=search_string) |
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
                "eol_reference_url": item.eol_reference_url
            })
        return json_data
