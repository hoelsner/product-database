"""
Django Project URL Configuration
"""
from django.views.generic.base import RedirectView
from django.conf.urls import include, url
from django.contrib import admin

admin.site.site_header = "Product Database Administration"

urlpatterns = [
    url(r'^productdb/admin/', include(admin.site.urls)),

    url(r'^productdb/api/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^productdb/', include('app.productdb.urls', namespace='productdb')),
    url(r'^$', RedirectView.as_view(url='/productdb/', permanent=False)),
]

handler404 = 'django_project.views.custom_page_not_found_view'
handler500 = 'django_project.views.custom_error_view'
handler400 = 'django_project.views.custom_bad_request_view'
handler403 = 'django_project.views.custom_permission_denied_view'
