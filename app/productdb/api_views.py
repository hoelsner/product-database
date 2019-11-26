from django.contrib.auth import logout
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework import filters
from rest_framework.authtoken.models import Token
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from app.config.models import NotificationMessage
from app.productdb.serializers import ProductSerializer, VendorSerializer, ProductGroupSerializer, ProductListSerializer, \
    ProductMigrationSourceSerializer, ProductMigrationOptionSerializer, NotificationMessageSerializer, \
    ProductIdNormalizationRuleSerializer
from app.productdb.models import Product, Vendor, ProductGroup, ProductList, ProductMigrationSource, \
    ProductMigrationOption, ProductIdNormalizationRule
from rest_framework import viewsets
from rest_framework.decorators import action


@method_decorator(name="list", decorator=swagger_auto_schema(
    tags=["User Interface"],
    operation_id="v1_notificationmessage_list",
    operation_description="list all Notification Message entries that are stored in the database"
))
@method_decorator(name="create", decorator=swagger_auto_schema(
    tags=["User Interface"],
    operation_id="v1_notificationmessage_create",
    operation_description="create a Notification Message entry"
))
@method_decorator(name="retrieve", decorator=swagger_auto_schema(
    tags=["User Interface"],
    operation_id="v1_notificationmessage_read",
    operation_description="get a Notification Message entry by `id`"
))
@method_decorator(name="destroy", decorator=swagger_auto_schema(
    tags=["User Interface"],
    operation_id="v1_notificationmessage_delete",
    operation_description="delete a Notification Message entry by `id`"
))
@method_decorator(name="update", decorator=swagger_auto_schema(
    tags=["User Interface"],
    operation_id="v1_notificationmessage_update",
    operation_description="update a Notification Message entry by `id`"
))
@method_decorator(name="partial_update", decorator=swagger_auto_schema(
    tags=["User Interface"],
    operation_id="v1_notificationmessage_partial_update",
    operation_description="partial update of a Notification Message entry by `id`"
))
class NotificationMessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for the Notification Message
    """
    queryset = NotificationMessage.objects.all().order_by("id")
    serializer_class = NotificationMessageSerializer
    lookup_field = "id"
    permission_classes = (permissions.DjangoModelPermissions,)


@method_decorator(name="list", decorator=swagger_auto_schema(
    tags=["Base Data"],
    operation_id="v1_vendor_list",
    operation_description="list all vendor entries that are stored in the database",
    manual_parameters=[
        openapi.Parameter("name", openapi.IN_QUERY, description="filter by Vendor name (exact match)", type=openapi.TYPE_STRING),
        openapi.Parameter("search", openapi.IN_QUERY, description="search Vendor Names using a regex string", type=openapi.TYPE_STRING),
    ]
))
@method_decorator(name="retrieve", decorator=swagger_auto_schema(
    tags=["Base Data"],
    operation_id="v1_vendor_read",
    operation_description="get a vendor entry by `id`",
))
class VendorViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for the Vendor objects"""
    queryset = Vendor.objects.all().order_by("id")
    serializer_class = VendorSerializer
    lookup_field = "id"
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_fields = ("id", "name")
    search_fields = ("$name",)
    permission_classes = (permissions.DjangoModelPermissions,)


@method_decorator(name="list", decorator=swagger_auto_schema(
    tags=["Product Migration Options"],
    operation_id="v1_productmigrationsource_list",
    operation_description="list all Product Migration Sources entries that are stored in the database",
    manual_parameters=[
        openapi.Parameter("name", openapi.IN_QUERY, description="filter by Product Migration Source name (exact match)", type=openapi.TYPE_STRING),
        openapi.Parameter("search", openapi.IN_QUERY, description="search within Product Migration Source name using a regex string", type=openapi.TYPE_STRING),
    ]
))
@method_decorator(name="retrieve", decorator=swagger_auto_schema(
    tags=["Product Migration Options"],
    operation_id="v1_productmigrationsource_read",
    operation_description="get a Product Migration Sources entry by `id`"
))
class ProductMigrationSourceViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for the ProductMigrationSource objects which identify a specific information source of a
    product migration"""
    queryset = ProductMigrationSource.objects.all().order_by("name")
    serializer_class = ProductMigrationSourceSerializer
    lookup_field = "id"
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_fields = ("id", "name")
    search_fields = ("$name",)
    permission_classes = (permissions.DjangoModelPermissions,)


class ProductMigrationOptionFilter(django_filters.FilterSet):
    product = django_filters.CharFilter(field_name="product__product_id", lookup_expr="exact")
    migration_source = django_filters.CharFilter(field_name="migration_source__name", lookup_expr="exact")
    replacement_product_id = django_filters.CharFilter(field_name="replacement_product_id", lookup_expr="exact")

    class Meta:
        model = ProductMigrationOption
        fields = ["id", "replacement_product_id", "migration_source", "product"]


@method_decorator(name="list", decorator=swagger_auto_schema(
    tags=["Product Migration Options"],
    operation_id="v1_productmigrationoption_list",
    operation_description="list all Product Migration Option entries that are stored in the database",
    manual_parameters=[
        openapi.Parameter("search", openapi.IN_QUERY, description="search within Replacement Product ID and Product ID using a regex string", type=openapi.TYPE_STRING),
    ]
))
@method_decorator(name="retrieve", decorator=swagger_auto_schema(
    tags=["Product Migration Options"],
    operation_id="v1_productmigrationoption_read",
    operation_description="get a Product Migration Option entry by `id`"
))
class ProductMigrationOptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for the ProductMigrationOption objects
    """
    queryset = ProductMigrationOption.objects.all().order_by("id")
    serializer_class = ProductMigrationOptionSerializer
    lookup_field = "id"
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_class = ProductMigrationOptionFilter
    search_fields = ("$replacement_product_id", "$product__product_id",)
    permission_classes = (permissions.DjangoModelPermissions,)


class ProductGroupFilter(django_filters.FilterSet):
    vendor = django_filters.CharFilter(field_name="vendor__name", lookup_expr="startswith")
    name = django_filters.CharFilter(field_name="name", lookup_expr="exact")

    class Meta:
        model = ProductGroup
        fields = ["id", "name", "vendor"]


@method_decorator(name="list", decorator=swagger_auto_schema(
    tags=["Base Data"],
    operation_id="v1_productgroup_list",
    operation_description="list all Product Group entries that are stored in the database",
    manual_parameters=[
        openapi.Parameter("search", openapi.IN_QUERY, description="search within Product Group Name using a regex string", type=openapi.TYPE_STRING),
    ]
))
@method_decorator(name="create", decorator=swagger_auto_schema(
    tags=["Base Data"],
    operation_id="v1_productgroup_create",
    operation_description="create a Product Group entry"
))
@method_decorator(name="retrieve", decorator=swagger_auto_schema(
    tags=["Base Data"],
    operation_id="v1_productgroup_read",
    operation_description="get a Product Group entry by `id`"
))
@method_decorator(name="destroy", decorator=swagger_auto_schema(
    tags=["Base Data"],
    operation_id="v1_productgroup_delete",
    operation_description="delete a Product Group entry by `id` (group value of associated Products are set to `None`)"
))
@method_decorator(name="update", decorator=swagger_auto_schema(
    tags=["Base Data"],
    operation_id="v1_productgroup_update",
    operation_description="update a Product Group entry by `id`"
))
@method_decorator(name="partial_update", decorator=swagger_auto_schema(
    tags=["Base Data"],
    operation_id="v1_productgroup_partial_update",
    operation_description="partial update of a Product Group entry by `id`"
))
class ProductGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint for the ProductGroup objects
    """
    queryset = ProductGroup.objects.all().order_by("name")
    serializer_class = ProductGroupSerializer
    lookup_field = "id"
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_class = ProductGroupFilter
    search_fields = ("$name",)
    permission_classes = (permissions.DjangoModelPermissions,)

    @swagger_auto_schema(
        tags=["Base Data"],
        operation_id="v1_productgroup_count",
        operation_description="amount of Product Groups",
        responses={
            status.HTTP_200_OK: openapi.Response(
                "response with count",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "count": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="amount of entries"
                        )
                    }
                )
            )
        }
    )
    @action(detail=False)
    def count(self, request):
        """
        returns the amount of Product Groups for the query
        """
        query = self.filter_queryset(self.get_queryset())
        result = {
            "count": query.count()
        }
        return Response(result)


class ProductListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    description = django_filters.CharFilter(field_name="description", lookup_expr="icontains")

    class Meta:
        model = ProductList
        fields = ["id", "name", "description"]


@method_decorator(name="list", decorator=swagger_auto_schema(
    tags=["Product Lists"],
    operation_id="v1_productlist_list",
    operation_description="list all Product List entries that are stored in the database"
))
@method_decorator(name="retrieve", decorator=swagger_auto_schema(
    tags=["Product Lists"],
    operation_id="v1_productlist_read",
    operation_description="get a Product List entry by `id`",
))
class ProductListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for the ProductList object
    """
    queryset = ProductList.objects.all().order_by("name")
    serializer_class = ProductListSerializer
    lookup_field = "id"
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_class = ProductListFilter
    permission_classes = (permissions.DjangoModelPermissions,)


class ProductFilter(django_filters.FilterSet):
    vendor = django_filters.CharFilter(field_name="vendor__name", lookup_expr="startswith")
    vendor__name = django_filters.CharFilter(field_name="vendor__name", lookup_expr="startswith")
    vendor__id = django_filters.NumberFilter(field_name="vendor")
    product_id = django_filters.CharFilter(field_name="product_id", lookup_expr="iexact")
    product_group = django_filters.CharFilter(field_name="product_group__name", lookup_expr="exact")
    product_group__name = django_filters.CharFilter(field_name="product_group__name", lookup_expr="exact")
    product_group__id = django_filters.NumberFilter(field_name="product_group")

    class Meta:
        model = Product
        fields = ["id", "product_id", "vendor", "product_group"]


@method_decorator(name="list", decorator=swagger_auto_schema(
    tags=["Base Data"],
    operation_id="v1_product_list",
    operation_description="list all Product entries that are stored in the database",
    manual_parameters=[
        openapi.Parameter("vendor", openapi.IN_QUERY, description="DEPRECATED, use `vendor__name` instead", type=openapi.TYPE_STRING),
        openapi.Parameter("vendor__name", openapi.IN_QUERY, description="filter by Vendor name (case-sensitive starts-with match)", type=openapi.TYPE_STRING),
        openapi.Parameter("vendor__id", openapi.IN_QUERY, description="filter by Vendor ID", type=openapi.TYPE_INTEGER),
        openapi.Parameter("product_id", openapi.IN_QUERY, description="filter by Product ID (case-insensitive exact match)", type=openapi.TYPE_STRING),
        openapi.Parameter("product_group", openapi.IN_QUERY, description="DEPRECATED, use `product_group__name` instead", type=openapi.TYPE_STRING),
        openapi.Parameter("product_group__name", openapi.IN_QUERY, description="filter by Product Group name (exact match)", type=openapi.TYPE_STRING),
        openapi.Parameter("product_group__id", openapi.IN_QUERY, description="filter by Product Group Database ID", type=openapi.TYPE_INTEGER),
        openapi.Parameter("search", openapi.IN_QUERY, description="search with Product ID, Description and tags field using a regex string", type=openapi.TYPE_STRING),
    ]
))
@method_decorator(name="create", decorator=swagger_auto_schema(
    tags=["Base Data"],
    operation_id="v1_product_create",
    operation_description="create a new Product entry"
))
@method_decorator(name="retrieve", decorator=swagger_auto_schema(
    tags=["Base Data"],
    operation_id="v1_product_read",
    operation_description="get a Product entry by `id`"
))
@method_decorator(name="destroy", decorator=swagger_auto_schema(
    tags=["Base Data"],
    operation_id="v1_product_delete",
    operation_description="delete a Product entry by `id` (with all associated replacements)"
))
@method_decorator(name="update", decorator=swagger_auto_schema(
    tags=["Base Data"],
    operation_id="v1_product_update",
    operation_description="update a Product entry by `id`"
))
@method_decorator(name="partial_update", decorator=swagger_auto_schema(
    tags=["Base Data"],
    operation_id="v1_product_partial_update",
    operation_description="partial update of a Product entry by `id`"
))
class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for the Product objects
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = "id"
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_class = ProductFilter
    search_fields = ("$product_id", "$description", "$tags")
    permission_classes = (permissions.DjangoModelPermissions,)

    @swagger_auto_schema(
        tags=["Base Data"],
        operation_id="v1_product_count",
        operation_description="amount of Products",
        responses={
            status.HTTP_200_OK: openapi.Response(
                "response with count",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "count": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="amount of entries"
                        )
                    }
                )
            )
        }
    )
    @action(detail=False)
    def count(self, request):
        """
        returns the amount of elements within the database
        """
        query = self.filter_queryset(self.get_queryset())
        result = {
            "count": query.count()
        }
        return Response(result)


class ProductIdNormalizationRuleFilter(django_filters.FilterSet):
    vendor_name = django_filters.CharFilter(field_name="vendor__name", lookup_expr="startswith")

    class Meta:
        model = ProductIdNormalizationRule
        fields = [
            "id",
            "vendor",
            "vendor_name"
        ]


@method_decorator(name="list", decorator=swagger_auto_schema(
    tags=["Product ID Normalization Rules"],
    operation_id="v1_productidnormalizationrule_list",
    operation_description="list all Product ID normalization rule entries that are stored in the database"
))
@method_decorator(name="retrieve", decorator=swagger_auto_schema(
    tags=["Product ID Normalization Rules"],
    operation_id="v1_productidnormalizationrule_read",
    operation_description="get a Product ID normalization rule entry by `id`"
))
class ProductIdNormalizationRuleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to match strings against a given input to map/normalize Product IDs
    """
    queryset = ProductIdNormalizationRule.objects.all()
    serializer_class = ProductIdNormalizationRuleSerializer
    filter_backends = (
        DjangoFilterBackend,
    )
    filter_class = ProductIdNormalizationRuleFilter
    permission_classes = (permissions.DjangoModelPermissions,)

    @swagger_auto_schema(
        tags=["Product ID Normalization Rules"],
        operation_id="v1_productidnormalizationrule_apply",
        manual_parameters=[
            openapi.Parameter("input_string", openapi.IN_QUERY, description="String that should be converted to a Product ID", type=openapi.TYPE_STRING),
            openapi.Parameter("vendor_name", openapi.IN_QUERY, description="Vendor Name (case-sensitive starts-with match) to use for the rule lookup (alternative to `vendor`)", type=openapi.TYPE_NUMBER),
            openapi.Parameter("vendor", openapi.IN_QUERY, description="Vendor ID to use for the rule lookup", type=openapi.TYPE_STRING),
            openapi.Parameter("id", openapi.IN_QUERY, description="(not implemented for this endpoint)", type=openapi.TYPE_NUMBER),
            openapi.Parameter("page", openapi.IN_QUERY, description="(not implemented for this endpoint)", type=openapi.TYPE_STRING),
            openapi.Parameter("page_size", openapi.IN_QUERY, description="(not implemented for this endpoint)", type=openapi.TYPE_STRING),
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                "lookup result",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "vendor_id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="ID of the vendor object that was used for the lookup"
                        ),
                        "product_id": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="either the converted string (if rules are applied) or the unmodified input string"
                        ),
                        "product_in_database": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Database ID for the product if the resulting string was found in the database, otherwise None"
                        ),
                        "matched_rule_id": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Database ID of the rule that matched the request"
                        )
                    }
                )
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                "invalid response (e.g. parameters missing)",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="error message"
                        )
                    }
                )
            )
        }
    )
    @action(detail=False, methods=["get"])
    def apply(self, request):
        """
        This endpoint provides a mechanism to convert well known string (e.g. from SNMP data) to a valid SKU based on configured rules per vendor. If nothing is matched, the input_string is returned unmodified.

        Try to normalize the input_string based on the configured rules for the given vendor_name, requires an `input_string` and a `vendor_name` or `vendor` id as `GET` parameter.
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
                product_id = rule.get_normalized_product_id(product_id)

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


class TokenLogoutApiView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Token.objects.filter(user=self.request.user)

    @action(detail=False)
    def post(self, request):
        """logout user and invalidate token"""
        try:
            request.user.auth_token.delete()

        except (AttributeError, ObjectDoesNotExist):
            pass

        logout(request)

        return Response(
            {"success": "Successfully logged out."},
            status=status.HTTP_200_OK
        )
