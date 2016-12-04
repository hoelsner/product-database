from django.contrib import admin

from app.config.models import NotificationMessage, TextBlock, ConfigOption


class ConfigOptionAdmin(admin.ModelAdmin):
    list_display = (
        "key",
        "value"
    )

admin.site.register(ConfigOption, ConfigOptionAdmin)


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


class TextBlockAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
    fields = (
        'name',
        'html_content'
    )

admin.site.register(TextBlock, TextBlockAdmin)
