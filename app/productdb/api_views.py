import django_filters
from rest_framework import permissions
from rest_framework import filters
from rest_framework.response import Response
from app.productdb.serializers import ProductSerializer, VendorSerializer, ProductGroupSerializer, ProductListSerializer, \
    ProductMigrationSourceSerializer, ProductMigrationOptionSerializer
from app.productdb.models import Product, Vendor, ProductGroup, ProductList, ProductMigrationSource, \
    ProductMigrationOption
from rest_framework import viewsets
from rest_framework.decorators import list_route


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
    product = django_filters.CharFilter(name="product__product_id", lookup_type="startswith")
    migration_source = django_filters.CharFilter(name="migration_source__name", lookup_type="startswith")
    replacement_product_id = django_filters.CharFilter(name="replacement_product_id", lookup_type="startswith")

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
    vendor = django_filters.CharFilter(name="vendor__name", lookup_type="startswith")
    name = django_filters.CharFilter(name="name", lookup_type="exact")

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
        ---
        omit_serializer: true
        parameters_strategy:
            form: replace
            query: merge
        """
        result = {
            "count": ProductGroup.objects.count()
        }
        return Response(result)


class ProductListFilter(filters.FilterSet):
    name = django_filters.CharFilter(name="name", lookup_type="icontains")
    description = django_filters.CharFilter(name="description", lookup_type="icontains")

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
    vendor = django_filters.CharFilter(name="vendor__name", lookup_type="startswith")
    product_id = django_filters.CharFilter(name="product_id", lookup_type="iexact")
    product_group = django_filters.CharFilter(name="product_group__name", lookup_type="exact")

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
        ---
        omit_serializer: true
        parameters_strategy:
            form: replace
            query: merge
        """
        result = {
            "count": Product.objects.count()
        }
        return Response(result)
