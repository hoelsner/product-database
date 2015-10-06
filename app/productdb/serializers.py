from rest_framework.serializers import ModelSerializer, SerializerMethodField, HyperlinkedModelSerializer
from rest_framework.serializers import ChoiceField, CharField, DecimalField, PrimaryKeyRelatedField
from django.core.validators import MinValueValidator
from app.productdb.models import Product, ProductList, Vendor, CURRENCY_CHOICES


class VendorSerializer(HyperlinkedModelSerializer):

    class Meta:
        model = Vendor
        fields = (
            'id',
            'name',
            'url'
        )
        extra_kwargs = {
            'url': {
                'lookup_field': 'id',
                'view_name': 'productdb:vendors-detail'
            }
        }
        depth = 0


class ProductListNameSerializer(ModelSerializer):

    class Meta:
        model = ProductList
        fields = (
            'id',
            'product_list_name',
        )
        depth = 0


class ProductLifecycleSerializer(HyperlinkedModelSerializer):

    class Meta:
        model = Product
        fields = (
            'id',
            'product_id',
            'description',
            'url',
            'eox_update_time_stamp',
            'end_of_sale_date',
            'end_of_support_date',
            'eol_ext_announcement_date',
            'end_of_sw_maintenance_date',
            'end_of_routine_failure_analysis',
            'end_of_service_contract_renewal',
            'end_of_new_service_attachment_date',
            'eol_reference_number',
            'eol_reference_url',
        )
        extra_kwargs = {
            'url': {
                'lookup_field': 'id',
                'view_name': 'productdb:products-detail'
            }
        }
        depth = 0


class ProductSerializer(HyperlinkedModelSerializer):
    currency = ChoiceField(
        choices=CURRENCY_CHOICES,
        initial="USD",
        required=False
    )
    description = CharField(
        initial="not set",
        required=False,
        style={'base_template': 'textarea.html'},
    )
    list_price = DecimalField(
        initial="0.00",
        required=False,
        allow_null=True,
        decimal_places=2,
        max_digits=32,
        help_text="list price of the element",
        validators=[MinValueValidator(0)]
    )

    # Read only, when PUT, 201 will be the result
    lists = SerializerMethodField(
        'product_list_names',
        read_only=True,
    )

    vendor = PrimaryKeyRelatedField(
        many=False,
        queryset=Vendor.objects.all(),
        read_only=False,
        required=False
    )

    @staticmethod
    def product_list_names(obj):
        return {
            product_list.product_list_name
            for product_list in obj.lists.all()
        }

    class Meta:
        model = Product
        fields = (
            'id',
            'product_id',
            'description',
            'list_price',
            'currency',
            'tags',
            'json_data',
            'lists',
            'vendor',
            'url',
            'eox_update_time_stamp',
            'end_of_sale_date',
            'end_of_support_date',
            'eol_ext_announcement_date',
            'end_of_sw_maintenance_date',
            'end_of_routine_failure_analysis',
            'end_of_service_contract_renewal',
            'end_of_new_service_attachment_date',
            'eol_reference_number',
            'eol_reference_url',
        )
        extra_kwargs = {
            'url': {
                'lookup_field': 'id',
                'view_name': 'productdb:products-detail'
            }
        }
        depth = 0


class ProductListSerializer(HyperlinkedModelSerializer):

    products = PrimaryKeyRelatedField(
        many=True,
        queryset=Product.objects.all(),
        read_only=False,
        required=False,
    )

    class Meta:
        model = ProductList
        fields = (
            'id',
            'product_list_name',
            'products',
            'url',
        )
        extra_kwargs = {
            'url': {
                'lookup_field': 'id',
                'view_name': 'productdb:productlists-detail'
            }
        }
        depth = 0
