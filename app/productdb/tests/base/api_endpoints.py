"""
Definition of the API endpoints for the unit tests
"""
from django.core.urlresolvers import reverse

PRODUCT_API_ENDPOINT = reverse("productdb:products-list")
PRODUCT_DETAIL_API_ENDPOINT = PRODUCT_API_ENDPOINT + "%i/"
PRODUCT_COUNT_API_ENDPOINT = PRODUCT_API_ENDPOINT + "count/"

VENDOR_API_ENDPOINT = reverse("productdb:vendors-list")
VENDOR_DETAIL_API_ENDPOINT = VENDOR_API_ENDPOINT + "%i/"

PRODUCT_GROUP_API_ENDPOINT = reverse("productdb:productgroups-list")
PRODUCT_GROUP_DETAIL_API_ENDPOINT = PRODUCT_GROUP_API_ENDPOINT + "%i/"
PRODUCT_GROUP_COUNT_API_ENDPOINT = PRODUCT_GROUP_API_ENDPOINT + "count/"
