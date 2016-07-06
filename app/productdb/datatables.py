from django_datatables_view.base_datatable_view import BaseDatatableView
from .models import Product
from django.db.models import Q
from app.productdb.utils import is_valid_regex


class VendorProductListJson(BaseDatatableView):
    # define column names that will be used in sorting
    # order is important and should be same as order of columns
    # displayed by datatables. For non sortable columns use empty
    # value like ''
    order_columns = [
        'product_id',
        'product_group',
        'description',
        'list_price',
        'tags'
    ]
    column_order = {
        "product_id": 0,
        "product_group": 1,
        "description": 2,
        "list_price": 3,
        "tags": 4
    }

    vendor_id = 0

    def get_initial_queryset(self):
        if self.kwargs['vendor_id']:
            self.vendor_id = self.kwargs['vendor_id']

        # return queryset used as base for further sorting/filtering
        # these are simply objects displayed in datatable
        return Product.objects.filter(vendor__id=self.vendor_id)

    def filter_queryset(self, qs):
        # use request parameters to filter queryset
        search_string = self.request.GET.get('search[value]', None)

        product_id_get_param = 'columns[' + str(self.column_order["product_id"]) + '][search][value]'
        product_group_get_param = 'columns[' + str(self.column_order["product_group"]) + '][search][value]'
        description_get_param = 'columns[' + str(self.column_order["description"]) + '][search][value]'
        list_price_get_param = 'columns[' + str(self.column_order["list_price"]) + '][search][value]'
        tags_get_param = 'columns[' + str(self.column_order["tags"]) + '][search][value]'

        product_id_search = self.request.GET.get(product_id_get_param, None)
        product_group_search = self.request.GET.get(product_group_get_param, None)
        description_search = self.request.GET.get(description_get_param, None)
        list_price_search = self.request.GET.get(list_price_get_param, None)
        tags_search = self.request.GET.get(tags_get_param, None)

        if search_string:
            # by default, the search field searched in the Product ID and the description field
            if is_valid_regex(search_string):
                qs = qs.filter(Q(product_id__regex=search_string) |
                               Q(description__regex=search_string))
            else:
                qs = qs.filter(Q(product_id__contains=search_string) |
                               Q(description__contains=search_string))

        if product_id_search:
            if is_valid_regex(product_id_search):
                qs = qs.filter(product_id__regex=product_id_search)
            else:
                qs = qs.filter(product_id__contains=product_id_search)

        if product_group_search:
            # the property for the product group is hidden in the class, therefore a "_" as prefix is required
            if is_valid_regex(product_group_search):
                qs = qs.filter(product_group__name__regex=product_group_search)
            else:
                qs = qs.filter(product_group__name__contains=product_group_search)

        if description_search:
            if is_valid_regex(description_search):
                qs = qs.filter(description__regex=description_search)
            else:
                qs = qs.filter(description__contains=description_search)

        if list_price_search:
            if is_valid_regex(list_price_search):
                qs = qs.filter(list_price__regex=list_price_search)
            else:
                qs = qs.filter(list_price__contains=list_price_search)

        if tags_search:
            if is_valid_regex(tags_search):
                qs = qs.filter(tags__regex=tags_search)
            else:
                qs = qs.filter(tags__contains=tags_search)

        return qs

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []

        for item in qs:
            json_data.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_group": item.product_group.name if item.product_group else "",
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
        'product_group',
        'description',
        'list_price',
        'tags'
    ]
    column_order = {
        "vendor": 0,
        "product_id": 1,
        "product_group": 2,
        "description": 3,
        "list_price": 4,
        "tags": 5
    }

    def get_initial_queryset(self):
        # return queryset used as base for further sorting/filtering
        # these are simply objects displayed in datatable
        return Product.objects.all()

    def filter_queryset(self, qs):
        # use request parameters to filter queryset
        search_string = self.request.GET.get('search[value]', None)

        vendor_get_param = 'columns[' + str(self.column_order["vendor"]) + '][search][value]'
        product_id_get_param = 'columns[' + str(self.column_order["product_id"]) + '][search][value]'
        product_group_get_param = 'columns[' + str(self.column_order["product_group"]) + '][search][value]'
        description_get_param = 'columns[' + str(self.column_order["description"]) + '][search][value]'
        list_price_get_param = 'columns[' + str(self.column_order["list_price"]) + '][search][value]'
        tags_get_param = 'columns[' + str(self.column_order["tags"]) + '][search][value]'

        vendor_search = self.request.GET.get(vendor_get_param, None)
        product_id_search = self.request.GET.get(product_id_get_param, None)
        product_group_search = self.request.GET.get(product_group_get_param, None)
        description_search = self.request.GET.get(description_get_param, None)
        list_price_search = self.request.GET.get(list_price_get_param, None)
        tags_search = self.request.GET.get(tags_get_param, None)

        if search_string:
            # by default, the search field searched in the Product ID and the description field
            if is_valid_regex(search_string):
                qs = qs.filter(Q(product_id__regex=search_string) |
                               Q(description__regex=search_string))
            else:
                qs = qs.filter(Q(product_id__contains=search_string) |
                               Q(description__contains=search_string))

        if vendor_search:
            if is_valid_regex(vendor_search):
                qs = qs.filter(vendor__name__regex=vendor_search)
            else:
                qs = qs.filter(vendor__name__contains=vendor_search)

        if product_id_search:
            if is_valid_regex(product_id_search):
                qs = qs.filter(product_id__regex=product_id_search)
            else:
                qs = qs.filter(product_id__contains=product_id_search)

        if product_group_search:
            # the property for the product group is hidden in the class, therefore a "_" as prefix is required
            if is_valid_regex(product_group_search):
                qs = qs.filter(product_group__name__regex=product_group_search)
            else:
                qs = qs.filter(product_group__name__contains=product_group_search)

        if description_search:
            if is_valid_regex(description_search):
                qs = qs.filter(description__regex=description_search)
            else:
                qs = qs.filter(description__contains=description_search)

        if list_price_search:
            if is_valid_regex(list_price_search):
                qs = qs.filter(list_price__regex=list_price_search)
            else:
                qs = qs.filter(list_price__contains=list_price_search)

        if tags_search:
            if is_valid_regex(tags_search):
                qs = qs.filter(tags__regex=tags_search)
            else:
                qs = qs.filter(tags__contains=tags_search)

        return qs

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here
        json_data = []

        for item in qs:
            json_data.append({
                "id": item.id,
                "vendor": item.vendor.name,
                "product_id": item.product_id,
                "product_group": item.product_group.name if item.product_group else "",
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
