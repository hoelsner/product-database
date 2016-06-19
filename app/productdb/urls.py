"""
Product Database URL configuration
"""
from django.conf.urls import include, url
from django.views.generic.base import RedirectView
from app.productdb import api_views
from app.productdb import views
from rest_framework import routers
import app.productdb.datatables as datatables

router = routers.DefaultRouter()
router.register(r'vendors', api_views.VendorViewSet, base_name="vendors")
router.register(r'products', api_views.ProductViewSet, base_name="products")

# namespace: productdb
urlpatterns = [
    # API related links
    url(r'^api-docs/', include('rest_framework_swagger.urls', namespace="apidocs")),
    url(r'^api/v0/', include(router.urls)),
    url(r'^api/$', RedirectView.as_view(url="v0/", permanent=False), name="api_redirect"),

    # Datatables endpoints
    url(
        r'^datatables/vendor_products/(?P<vendor_id>[0-9]+)/$',
        datatables.VendorProductListJson.as_view(),
        name='datatables_vendor_products_endpoint'
    ),
    url(
        r'^datatables/vendor_products/$',
        datatables.VendorProductListJson.as_view(),
        name='datatables_vendor_products_view'
    ),
    url(
        r'^datatables/product_data/$',
        datatables.ListProductsJson.as_view(),
        name='datatables_list_products_view'
    ),

    # user views
    url(r'^vendor/$', views.browse_vendor_products, name='browse_vendor_products'),
    url(r'^products/$', views.browse_all_products, name='all_products'),
    url(r'^product/$', views.view_product_details, name='product-list'),
    url(r'^product/(?P<product_id>\d+)/$', views.view_product_details, name='product-detail'),
    url(r'^do/bulkcheck/$', views.bulk_eol_check, name='bulk_eol_check'),
    url(r'^import/products/$', views.import_products, name='import_products'),
    url(r'^about/$', views.about_view, name='about'),
    url(r'^$', views.home, name='home'),
]

