from rest_framework.response import Response
from app.productdb.serializers import ProductSerializer, VendorSerializer
from app.productdb.models import Product, Vendor
from rest_framework import viewsets
from rest_framework.decorators import list_route
import json


class VendorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for the Vendor objects
    """
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    lookup_field = 'id'

    @list_route(methods=['POST'], )
    def byname(self, request):
        """
        get entire vendor object by vendor name
        ---
        parameters_strategy:
            form: replace
            query: merge
        parameters:
            - name: name
              description: name of the vendor (unique in model)
              required: true
              type: string
        """
        if "application/json" in request.META['CONTENT_TYPE']:
            request_json = json.loads(request.body.decode("utf-8"))
        else:
            request_json = request.POST

        result = dict()
        if "name" in request_json.keys():
            vendor_name = request_json['name']
            query_result = Vendor.objects.filter(name=vendor_name)
            if query_result.count() == 0:
                result['name'] = "Vendor name '%s' not found" % vendor_name
                return Response(result, status=404)
            result = VendorSerializer(query_result.get(), context={'request': request})
            return Response(result.data, status=200)
        else:
            result['error'] = "invalid parameter given, 'name' required"
            return Response(result, status=400)


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for the Product objects
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'id'

    @list_route(methods=['POST'], )
    def byname(self, request):
        """
        get entire product object by product name
        ---
        parameters_strategy:
            form: replace
            query: merge
        parameters:
            - name: product_id
              description: name of the product (unique in model)
              required: true
              type: string
        """
        result = dict()
        if "application/json" in request.META['CONTENT_TYPE']:
            request_json = json.loads(request.body.decode("utf-8"))
        else:
            request_json = request.POST

        if "product_id" in request_json.keys():
            product_id = request_json['product_id']
            query_result = Product.objects.filter(product_id=product_id)
            if query_result.count() == 0:
                result['product_id'] = "Product name '%s' not found" % product_id
                return Response(result, status=404)
            result = ProductSerializer(query_result.get(), context={'request': request})
            return Response(result.data, status=200)
        else:
            result['error'] = "invalid parameter given, 'product_id' required"
            return Response(result, status=400)

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
