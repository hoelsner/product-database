"""
Definition of the API endpoints for the unit tests
"""
from django.core.urlresolvers import reverse

PRODUCT_API_ENDPOINT = reverse("productdb:products-list")
PRODUCT_DETAIL_API_ENDPOINT = PRODUCT_API_ENDPOINT + "%i/"
PRODUCT_BY_NAME_API_ENDPOINT = PRODUCT_API_ENDPOINT + "byname/"
PRODUCT_COUNT_API_ENDPOINT = PRODUCT_API_ENDPOINT + "count/"

VENDOR_API_ENDPOINT = reverse("productdb:vendors-list")
VENDOR_DETAIL_API_ENDPOINT = VENDOR_API_ENDPOINT + "%i/"
VENDOR_PRODUCTS_DATA_API_ENDPOINT = VENDOR_API_ENDPOINT + "%i/products_data/"
VENDOR_BY_NAME_API_ENDPOINT = VENDOR_API_ENDPOINT + "byname/"
