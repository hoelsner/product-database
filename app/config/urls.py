"""
Product Database Config URL configuration (namespace "productdb_config")
"""
from django.conf.urls import url
from app.config import views

# namespace: productdb_config
urlpatterns = [
    # user views
    url(r'^change/$', views.change_configuration, name='change_settings'),
    url(r'^status/$', views.status, name='status'),
    url(r'^flush_cache/$', views.flush_cache, name='flush_cache'),
    url(r'^messages/$', views.server_messages_list, name='notification-list'),
    url(r'^messages/add/$', views.add_notification, name='notification-add'),
    url(r'^messages/(?P<message_id>\d+)/$', views.server_message_detail, name='notification-detail'),
]

app_name = "config"
