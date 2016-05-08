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

urlpatterns = [
    url(r'^api-docs/', include('rest_framework_swagger.urls', namespace="apidocs")),
    url(r'^api/v0/', include(router.urls)),
    # redirect to current
    url(r'^api/$', RedirectView.as_view(url="v0/", permanent=False), name="api_redirect"),

    # endpoints for datatables
    url(r'^datatables/lifecycle/$',
        datatables.LifecycleListJson.as_view(),
        name='datatables_lifecycle_view'),
    url(r'^datatables/lifecycle/(?P<vendor_id>[0-9]+)/$',
        datatables.LifecycleListJson.as_view(),
        name='datatables_lifecycle_endpoint'),

    url(r'^datatables/vendor_products/$',
        datatables.VendorProductListJson.as_view(),
        name='datatables_vendor_products_view'),
    url(r'^datatables/vendor_products/(?P<vendor_id>[0-9]+)/$',
        datatables.VendorProductListJson.as_view(),
        name='datatables_vendor_products_endpoint'),

    url(r'^datatables/product_lists_data/$',
        datatables.ListProductsJson.as_view(),
        name='datatables_list_products_view'),
    url(r'^datatables/product_lists_data/(?P<product_list_id>[0-9]+)/$',
        datatables.ListProductsJson.as_view(),
        name='datatables_list_products_endpoint'),

    # schedule tasks now
    url(r'schedule/cisco_eox_api_sync',
        views.schedule_cisco_eox_api_sync_now,
        name="schedule_cisco_eox_api_sync_now"),

    url(r'^vendor/$', views.browse_vendor_products, name='browse_vendor_products'),
    url(r'^lifecycle/bulkcheck/$', views.bulk_eol_check, name='bulk_eol_check'),
    url(r'^lifecycle/$', views.browse_product_lifecycle_information, name='browse_product_lifecycle_information'),
    url(r'^settings/crawler/ciscoapi/$', views.cisco_api_settings, name='cisco_api_settings'),
    url(r'^settings/crawler/overview/$', views.crawler_overview, name='crawler_overview'),
    url(r'^settings/testtools/$', views.test_tools, name='test_tools'),
    url(r'^settings/$', views.settings_view, name='settings'),
    url(r'^import/products/$', views.import_products, name='import_products'),
    url(r'^about/$', views.about_view, name='about'),
    url(r'^$', views.home, name='home'),
]

