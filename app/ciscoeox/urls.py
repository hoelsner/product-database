"""
Cisco EoX API URL configuration (namespace "cisco_api")
"""
from django.conf.urls import url
from app.ciscoeox import views

# namespace: cisco_api
urlpatterns = [
    url(r'^sync/eox/$', views.start_cisco_eox_api_sync_now, name='start_cisco_eox_api_sync_now'),
]
