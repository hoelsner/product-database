from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class NotificationMessage(models.Model):
    """
    Notifications from certain processes
    """
    MESSAGE_ERROR = "ERR"
    MESSAGE_INFO = "INFO"
    MESSAGE_SUCCESS = "SUCC"
    MESSAGE_WARNING = "WARN"

    MESSAGE_TYPE = (
        ("INFO", "info"),
        ("SUCC", "success"),
        ("ERR", "error"),
        ("WARN", "warning"),
    )

    title = models.CharField(
        max_length=2048
    )

    type = models.CharField(
        max_length=8,
        choices=MESSAGE_TYPE,
        default=MESSAGE_INFO
    )

    summary_message = models.TextField(
        max_length=16384
    )

    detailed_message = models.TextField(
        max_length=16384
    )

    created = models.DateTimeField(
        auto_now_add=True,
        editable=False
    )

    @staticmethod
    def add_info_message(title, summary_message, detailed_message):
        NotificationMessage.objects.create(
            title=title,
            type=NotificationMessage.MESSAGE_INFO,
            summary_message=summary_message,
            detailed_message=detailed_message
        )

    @staticmethod
    def add_success_message(title, summary_message, detailed_message):
        NotificationMessage.objects.create(
            title=title,
            type=NotificationMessage.MESSAGE_SUCCESS,
            summary_message=summary_message,
            detailed_message=detailed_message
        )

    @staticmethod
    def add_warning_message(title, summary_message, detailed_message):
        NotificationMessage.objects.create(
            title=title,
            type=NotificationMessage.MESSAGE_WARNING,
            summary_message=summary_message,
            detailed_message=detailed_message
        )

    @staticmethod
    def add_error_message(title, summary_message, detailed_message):
        NotificationMessage.objects.create(
            title=title,
            type=NotificationMessage.MESSAGE_ERROR,
            summary_message=summary_message,
            detailed_message=detailed_message
        )

    def save(self, *args, **kwargs):
        # clean the object before save
        self.full_clean()
        super(NotificationMessage, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('created',)


class TextBlock(models.Model):
    """
    Dynamic content at some page views
    """
    TB_HOMEPAGE_TEXT_BEFORE_FAVORITE_ACTIONS = "Homepage text before favorite actions"
    TB_HOMEPAGE_TEXT_AFTER_FAVORITE_ACTIONS = "Homepage text after favorite actions"

    name = models.CharField(
        max_length=512,
        unique=True,
        verbose_name="Name",
        help_text="Internal name for the Text Block (predefined)",
    )

    html_content = models.TextField(
        max_length=16384,
        verbose_name="HTML content",
        help_text="content of the text block (HTML possible)",
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        # clean the object before save
        self.full_clean()
        super(TextBlock, self).save(*args, **kwargs)


class ConfigOption(models.Model):
    GLOBAL_CISCO_API_ENABLED = "global.cisco_api_enabled"
    GLOBAL_LOGIN_ONLY_MODE = "global.login_only_mode"
    GLOBAL_INTERNAL_PRODUCT_ID_LABEL = "global.internal_product_id_label"
    CISCO_API_CLIENT_ID = "cisco_api.client_id"
    CISCO_API_CLIENT_SECRET = "cisco_api.client_secret"
    CISCO_EOX_CRAWLER_AUTO_SYNC = "cisco_eox.auto_sync"
    CISCO_EOX_CRAWLER_CREATE_PRODUCTS = "cisco_eox.create_products"
    CISCO_EOX_CRAWLER_LAST_EXECUTION_TIME = "cisco_eox.last_execution_time"
    CISCO_EOX_CRAWLER_LAST_EXECUTION_RESULT = "cisco_eox.last_execution_result"
    CISCO_EOX_API_QUERIES = "cisco_eox.api_queries"
    CISCO_EOX_PRODUCT_BLACKLIST_REGEX = "cisco_eox.product_blacklist_regex"
    CISCO_EOX_WAIT_TIME = "cisco_eox.wait_time_between_queries"

    key = models.CharField(
        max_length=256,
        unique=True
    )

    value = models.CharField(
        max_length=8192,
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        self.value = str(self.value).strip() if self.value else None
        self.key = self.key.strip() if self.key else None
        self.full_clean()
        super(ConfigOption, self).save(*args, **kwargs)

    def __str__(self):
        return self.key


@receiver(post_save, sender=NotificationMessage)
def invalidate_notification_message_related_cache_values(sender, instance, **kwargs):
    """delete cache values that are somehow related to the Notification Message data model"""
    cache.delete("PDB_HOMEPAGE_CONTEXT")
