from rest_framework.serializers import HyperlinkedModelSerializer, BooleanField
from rest_framework import serializers
from rest_framework.serializers import ChoiceField, CharField, DecimalField, PrimaryKeyRelatedField
from django.core.validators import MinValueValidator
from app.productdb.models import Product, Vendor, CURRENCY_CHOICES, ProductGroup, ProductList, ProductMigrationSource, \
    ProductMigrationOption


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


class ProductGroupSerializer(HyperlinkedModelSerializer):
    vendor = PrimaryKeyRelatedField(
        many=False,
        queryset=Vendor.objects.all(),
        read_only=False,
        required=False
    )

    class Meta:
        model = ProductGroup
        fields = (
            'id',
            'name',
            'vendor',
            'url'
        )
        extra_kwargs = {
            'url': {
                'lookup_field': 'id',
                'view_name': 'productdb:productgroups-detail'
            }
        }
        depth = 0


class ProductListItemField(serializers.Field):
    def to_representation(self, value):
        return value.split("\n")


class ProductListSerializer(HyperlinkedModelSerializer):
    """Read only Product List endpoint"""
    contact_email = serializers.SerializerMethodField(
        'get_update_user_email',
        read_only=True,
        required=False
    )

    string_product_list = ProductListItemField(read_only=True)

    def get_update_user_email(self, obj):
        """returns the email address of the update user or an empty string"""
        return obj.update_user.email

    class Meta:
        model = ProductList
        fields = (
            "id",
            "name",
            "description",
            "string_product_list",
            "update_date",
            "contact_email",
            "url"
        )
        extra_kwargs = {
            "url": {
                "lookup_field": "id",
                "view_name": "productdb:productlists-detail"
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
        allow_blank=True,
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

    lc_state_sync = BooleanField(
        required=False,
        initial=False,
        read_only=True,
        help_text="automatic synchronization of lifecycle states"
    )

    product_group = PrimaryKeyRelatedField(
        many=False,
        queryset=ProductGroup.objects.all(),
        read_only=False,
        required=False,
        allow_null=True
    )

    vendor = PrimaryKeyRelatedField(
        many=False,
        queryset=Vendor.objects.all(),
        read_only=False,
        required=False
    )

    def validate_product_group(self, value):
        """
        verify that the product group is associated to the same vendor as the product
        """
        if value and self.instance:  # check for None type
            if value.vendor.name != self.instance.vendor.name:
                raise serializers.ValidationError(
                    "Invalid product group, group and product must be associated to the same vendor"
                )
        return value

    class Meta:
        model = Product
        fields = (
            'id',
            'product_id',
            'description',
            'list_price',
            'currency',
            'tags',
            'vendor',
            'product_group',
            'url',
            'eox_update_time_stamp',
            'end_of_sale_date',
            'end_of_support_date',
            'eol_ext_announcement_date',
            'end_of_sw_maintenance_date',
            'end_of_routine_failure_analysis',
            'end_of_service_contract_renewal',
            'end_of_new_service_attachment_date',
            'end_of_sec_vuln_supp_date',
            'eol_reference_number',
            'eol_reference_url',
            'lc_state_sync',
            'internal_product_id',
            'update_timestamp',
            'list_price_timestamp',
        )
        extra_kwargs = {
            'url': {
                'lookup_field': 'id',
                'view_name': 'productdb:products-detail'
            }
        }
        depth = 0


class ProductMigrationOptionSerializer(HyperlinkedModelSerializer):
    product = PrimaryKeyRelatedField(
        many=False,
        queryset=Product.objects.all(),
        read_only=False,
        required=False
    )
    migration_source = PrimaryKeyRelatedField(
        many=False,
        queryset=ProductMigrationSource.objects.all(),
        read_only=False,
        required=False
    )

    class Meta:
        model = ProductMigrationOption
        fields = (
            "id",
            "product",
            "migration_source",
            "comment",
            "migration_product_info_url",
            "replacement_product_id",
            "url"
        )
        extra_kwargs = {
            "url": {
                "lookup_field": "id",
                "view_name": "productdb:productmigrationoptions-detail"
            }
        }
        depth = 0


class ProductMigrationSourceSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = ProductMigrationSource
        fields = (
            "id",
            "name",
            "description",
            "preference",
            "url",
        )
        extra_kwargs = {
            "url": {
                "lookup_field": "id",
                "view_name": "productdb:productmigrationsources-detail"
            }
        }
        depth = 0
