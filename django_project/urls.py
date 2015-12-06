"""src URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.views.generic.base import RedirectView
from django.conf.urls import include, url
from django.contrib import admin

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
