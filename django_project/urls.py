"""
Django Project URL Configuration
"""
from django.conf import settings
from django.views.generic.base import RedirectView
from django.conf.urls import include, url
from django.contrib import admin
from django_project import views

admin.site.site_header = "Product Database Administration"

urlpatterns = [
    url(r'^productdb/admin/', include(admin.site.urls)),

    # common views for the application
    url(r"^productdb/task/watch/(?P<task_id>.*)", views.task_status_ajax, name="task_state"),
    url(r"^productdb/task/(?P<task_id>.*)", views.task_progress_view, name="task_in_progress"),
    url(r'^productdb/login/$', views.login_user, name="login"),
    url(r'^productdb/logout/$', views.logout_user, name="logout"),
    url(r'^productdb/change-password/', views.custom_password_change, name="change_password"),
    url(r'^productdb/change-done/', views.custom_password_change_done, name="custom_password_change_done"),

    url(r'^productdb/config/', include('app.config.urls', namespace='productdb_config')),
    url(r'^productdb/ciscoapi/', include('app.ciscoeox.urls', namespace='cisco_api')),
    url(r'^productdb/', include('app.productdb.urls', namespace='productdb')),
    url(r'^$', RedirectView.as_view(url='/productdb/', permanent=False)),
]

handler404 = 'django_project.views.custom_page_not_found_view'
handler500 = 'django_project.views.custom_error_view'
handler400 = 'django_project.views.custom_bad_request_view'
handler403 = 'django_project.views.custom_permission_denied_view'

# enable django debug toolbar if DEBUG mode is enabled
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
