from rest_framework.response import Response
from app.productdb.serializers import ProductSerializer, ProductListSerializer, VendorSerializer
from app.productdb.models import Product, ProductList, Vendor
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
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
        result = ""
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

    @detail_route(methods=['GET'], )
    def meta(self, request, id):
        """
        API endpoint to get an data array with all products from the given list
        ---
        parameters_strategy:
            form: replace
            query: merge
        """
        try:
            product = Product.objects.get(id=id)
            if product.json_data:
                result = product.json_data
            else:
                result = []

            return Response(result, status=200)

        except Exception as ex:
            print(ex)
            return Response(status=404)


class ProductListViewSet(viewsets.ModelViewSet):
    """
    API endpoint for the ProductList objects
    """
    queryset = ProductList.objects.all()
    serializer_class = ProductListSerializer
    lookup_field = 'id'

    @detail_route(methods=['GET'], )
    def namedproducts(self, request, id):
        """
        get entire product list object with named products list (read only)
        ---
        parameters_strategy:
            form: replace
            query: merge
        """
        product_list = self.get_object()
        pl_json = ProductListSerializer(product_list, context={'request': request}).data
        # overwrite the products element with a list of names
        product_names = []
        for product in pl_json['products']:
            product = Product.objects.get(id=product)
            product_names.append(product.product_id)

        product_names.sort()
        pl_json['products'] = product_names
        return Response(pl_json, status=200)

    @list_route(methods=['POST'], )
    def byname(self, request):
        """
        get entire product list object by product list name
        ---
        parameters_strategy:
            form: replace
            query: merge
        parameters:
            - name: product_list_name
              description: name of the product list (unique in model)
              required: true
              type: string
        """
        result = dict()
        if "application/json" in request.META['CONTENT_TYPE']:
            request_json = json.loads(request.body.decode("utf-8"))
        else:
            request_json = request.POST

        if "product_list_name" in request_json.keys():
            product_list_name = request_json['product_list_name']
            query_result = ProductList.objects.filter(product_list_name=product_list_name)
            if query_result.count() == 0:
                result['product_list_name'] = "Product list name '%s' not found" % product_list_name
                return Response(result, status=404)
            result = ProductListSerializer(query_result.get(), context={'request': request})
            return Response(result.data, status=200)
        else:
            result['error'] = "invalid parameter given, 'product_list_name' required"
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
            "count": ProductList.objects.count()
        }
        return Response(result)
