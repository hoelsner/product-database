from django.contrib import admin

from app.config.models import NotificationMessage


class NotificationMessageAdmin(admin.ModelAdmin):
    list_display = (
        'type',
        'title',
        'summary_message',
        'created',
    )

    search_fields = (
        'title',
        'summary_message',
        'detailed_message',
    )

admin.site.register(NotificationMessage, NotificationMessageAdmin)
