"""
Cisco API URL configuration
"""
from django.conf.urls import url
from app.ciscoeox import views

# namespace: cisco_api
urlpatterns = [
    # user views
    url(r'^query/eox/$', views.cisco_eox_query, name='eox_query'),
    url(r'^sync/eox/$', views.start_cisco_eox_api_sync_now, name='start_cisco_eox_api_sync_now'),
]
