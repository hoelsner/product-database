import django_filters
from rest_framework import permissions
from rest_framework import filters
from rest_framework.response import Response
from app.productdb.serializers import ProductSerializer, VendorSerializer
from app.productdb.models import Product, Vendor
from rest_framework import viewsets
from rest_framework.decorators import list_route


class VendorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for the Vendor objects
    """
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    lookup_field = 'id'
    filter_backends = (
        filters.DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_fields = ('id', 'name')
    search_fields = ('$name',)
    permission_classes = (permissions.DjangoModelPermissions,)


class ProductFilter(filters.FilterSet):
    vendor = django_filters.CharFilter(name="vendor__name", lookup_type="startswith")
    product_id = django_filters.CharFilter(name="product_id", lookup_type="iexact")

    class Meta:
        model = Product
        fields = ['id', 'product_id', 'vendor']


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
