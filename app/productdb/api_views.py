import django_filters
from rest_framework import permissions, status
from rest_framework import filters
from rest_framework.response import Response

from app.config.models import NotificationMessage
from app.productdb.serializers import ProductSerializer, VendorSerializer, ProductGroupSerializer, ProductListSerializer, \
    ProductMigrationSourceSerializer, ProductMigrationOptionSerializer, NotificationMessageSerializer, \
    ProductIdNormalizationRuleSerializer
from app.productdb.models import Product, Vendor, ProductGroup, ProductList, ProductMigrationSource, \
    ProductMigrationOption, ProductIdNormalizationRule
from rest_framework import viewsets
from rest_framework.decorators import list_route


class NotificationMessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for the Notification Message
    """
    queryset = NotificationMessage.objects.all().order_by("id")
    serializer_class = NotificationMessageSerializer
    lookup_field = 'id'
    permission_classes = (permissions.DjangoModelPermissions,)


class VendorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for the Vendor objects
    """
    queryset = Vendor.objects.all().order_by("id")
    serializer_class = VendorSerializer
    lookup_field = 'id'
    filter_backends = (
        filters.DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_fields = ('id', 'name')
    search_fields = ('$name',)
    permission_classes = (permissions.DjangoModelPermissions,)


class ProductMigrationSourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for the ProductMigrationSource objects
    """
    queryset = ProductMigrationSource.objects.all().order_by("name")
    serializer_class = ProductMigrationSourceSerializer
    lookup_field = 'id'
    filter_backends = (
        filters.DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_fields = ('id', 'name')
    search_fields = ('$name',)
    permission_classes = (permissions.DjangoModelPermissions,)


class ProductMigrationOptionFilter(filters.FilterSet):
    product = django_filters.CharFilter(name="product__product_id", lookup_expr="startswith")
    migration_source = django_filters.CharFilter(name="migration_source__name", lookup_expr="startswith")
    replacement_product_id = django_filters.CharFilter(name="replacement_product_id", lookup_expr="startswith")

    class Meta:
        model = ProductMigrationOption
        fields = ['id', 'replacement_product_id', 'migration_source', 'product']


class ProductMigrationOptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for the ProductMigrationOption objects
    """
    queryset = ProductMigrationOption.objects.all().order_by("id")
    serializer_class = ProductMigrationOptionSerializer
    lookup_field = 'id'
    filter_backends = (
        filters.DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_class = ProductMigrationOptionFilter
    search_fields = ('$replacement_product_id', '$product__product_id',)
    permission_classes = (permissions.DjangoModelPermissions,)


class ProductGroupFilter(filters.FilterSet):
    vendor = django_filters.CharFilter(name="vendor__name", lookup_expr="startswith")
    name = django_filters.CharFilter(name="name", lookup_expr="exact")

    class Meta:
        model = ProductGroup
        fields = ['id', 'name', 'vendor']


class ProductGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint for the ProductGroup objects
    """
    queryset = ProductGroup.objects.all().order_by("name")
    serializer_class = ProductGroupSerializer
    lookup_field = 'id'
    filter_backends = (
        filters.DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_class = ProductGroupFilter
    search_fields = ('$name',)
    permission_classes = (permissions.DjangoModelPermissions,)

    @list_route()
    def count(self, request):
        """
        returns the amount of elements within the database
        """
        result = {
            "count": ProductGroup.objects.count()
        }
        return Response(result)


class ProductListFilter(filters.FilterSet):
    name = django_filters.CharFilter(name="name", lookup_expr="icontains")
    description = django_filters.CharFilter(name="description", lookup_expr="icontains")

    class Meta:
        model = ProductList
        fields = ['id', 'name', 'description']


class ProductListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for the ProductList object
    """
    queryset = ProductList.objects.all().order_by("name")
    serializer_class = ProductListSerializer
    lookup_field = "id"
    filter_backends = (
        filters.DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_class = ProductListFilter
    permission_classes = (permissions.DjangoModelPermissions,)


class ProductFilter(filters.FilterSet):
    vendor = django_filters.CharFilter(name="vendor__name", lookup_expr="startswith")
    product_id = django_filters.CharFilter(name="product_id", lookup_expr="iexact")
    product_group = django_filters.CharFilter(name="product_group__name", lookup_expr="exact")

    class Meta:
        model = Product
        fields = ['id', 'product_id', 'vendor', 'product_group']


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for the Product objects
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'id'
    filter_backends = (
        filters.DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_class = ProductFilter
    search_fields = ('$product_id', '$description', '$tags')
    permission_classes = (permissions.DjangoModelPermissions,)

    @list_route()
    def count(self, request):
        """
        returns the amount of elements within the database
        """
        result = {
            "count": Product.objects.count()
        }
        return Response(result)


class ProductIdNormalizationRuleFilter(filters.FilterSet):
    vendor_name = django_filters.CharFilter(name="vendor__name", lookup_expr="startswith")

    class Meta:
        model = ProductIdNormalizationRule
        fields = [
            "id",
            "vendor",
            "vendor_name"
        ]


class ProductIdNormalizationRuleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to match strings against a given input to map/normalize Product IDs
    """
    queryset = ProductIdNormalizationRule.objects.all()
    serializer_class = ProductIdNormalizationRuleSerializer
    filter_backends = (
        filters.DjangoFilterBackend,
    )
    filter_class = ProductIdNormalizationRuleFilter
    permission_classes = (permissions.DjangoModelPermissions,)

    @list_route(methods=["get"])
    def apply(self, request):
        """
        try to normalize the input_string based on the configured rules for the given vendor_name, requires
        an `input_string` and a `vendor_name` or `vendor` id as `GET` parameter.
        """
        input_string = request.GET.get("input_string", None)
        vendor_name = request.GET.get("vendor_name", None)

        if not input_string or not vendor_name:
            return Response({
                "error": "input_string and vendor_name parameter required"
            }, status=status.HTTP_400_BAD_REQUEST)

        # lookup vendor
        vendor_qs = Vendor.objects.filter(name__startswith=vendor_name)
        vendor_count = vendor_qs.count()
        if vendor_count == 0:
            return Response({
                "error": "vendor_name returns no result"
            }, status=status.HTTP_400_BAD_REQUEST)

        elif vendor_count > 1:
            return Response({
                "error": "vendor_name not unique, multiple entries found"
            }, status=status.HTTP_400_BAD_REQUEST)

        vendor = vendor_qs.first()
        product_id = input_string
        product_in_database = None
        matched_rule = None

        # apply rules on input string
        rules = ProductIdNormalizationRule.objects.filter(vendor=vendor).order_by("priority").order_by("product_id")
        for rule in rules:
            if rule.matches(input_string):
                product_id = rule.product_id

                # lookup in local database
                pqs = Product.objects.filter(product_id=product_id, vendor=vendor)
                if pqs.count() != 0:
                    product_in_database = pqs.first().id

                matched_rule = rule.id
                break

        return Response({
            "vendor_id": vendor.id,
            "product_id": product_id,
            "product_in_database": product_in_database,
            "matched_rule_id": matched_rule
        }, status=status.HTTP_200_OK)
