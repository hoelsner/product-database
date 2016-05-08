from django.core.validators import MinValueValidator
from django.db import models
from annoying.fields import JSONField

from app.productdb.validators import validate_json

# choices for the currency
CURRENCY_CHOICES = (
    ('EUR', 'Euro'),
    ('USD', 'US-Dollar'),
)


class Vendor(models.Model):
    """
    Vendor object which is assigned to a Product
    """
    name = models.CharField(
        max_length=128,
        unique=True
    )

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    def delete(self, using=None):
        # prevent the deletion of the "unassigned" value from model
        if self.id == 0:
            raise Exception("Operation not allowed")
        super().delete(using)

    class Meta:
        ordering = ('name',)


class Product(models.Model):
    # Used as Primary Key
    product_id = models.TextField(
        unique=True,
        help_text="Unique Product ID"
    )

    description = models.TextField(
        default="not set",
        help_text="description of the product"
    )

    list_price = models.DecimalField(
        null=True,
        blank=True,
        decimal_places=2,
        max_digits=32,
        help_text="list price of the element",
        validators=[MinValueValidator(0)]
    )

    currency = models.TextField(
        max_length=16,
        choices=CURRENCY_CHOICES,
        default="USD",
        help_text="currency of the list price"
    )

    tags = models.TextField(
        default="",
        blank=True,
        help_text="unformatted tag field"
    )

    vendor = models.ForeignKey(
        Vendor,
        blank=False,
        null=False,
        default=0,
        help_text="vendor name",
        on_delete=models.SET_DEFAULT
    )

    eox_update_time_stamp = models.DateField(
        null=True,
        blank=True,
        help_text="EoX lifecycle data update time stamp (set with automatic synchronization)"
    )

    eol_ext_announcement_date = models.DateField(
        null=True,
        blank=True,
        help_text="external EoX announcement date"
    )

    end_of_sale_date = models.DateField(
        null=True,
        blank=True,
        help_text="End of Sale date"
    )

    end_of_new_service_attachment_date = models.DateField(
        null=True,
        blank=True,
        help_text="End of new Service Attachment date"
    )

    end_of_sw_maintenance_date = models.DateField(
        null=True,
        blank=True,
        help_text="End of Software Maintenance date"
    )

    end_of_routine_failure_analysis = models.DateField(
        null=True,
        blank=True,
        help_text="End of Routine Failure analysis"
    )

    end_of_service_contract_renewal = models.DateField(
        null=True,
        blank=True,
        help_text="End of Service Contract renewal date"
    )

    end_of_support_date = models.DateField(
        null=True,
        blank=True,
        help_text="End of Support (Last day of support) date",
    )

    eol_reference_number = models.TextField(
        null=True,
        blank=True,
        help_text="Product bulletin number or vendor specific reference for EoL"
    )

    eol_reference_url = models.URLField(
        null=True,
        blank=True,
        help_text="URL to the Product bulletin or EoL reference"
    )

    def __str__(self):
        return self.product_id

    def __unicode__(self):
        return self.product_id

    class Meta:
        ordering = ('product_id',)


class Settings(models.Model):
    cisco_api_enabled = models.BooleanField(
        default=False,
        help_text="Indicates the availability of the Cisco API access"
    )

    cisco_eox_api_auto_sync_enabled = models.BooleanField(
        default=False,
        help_text="Enable the automatic synchronization of the Cisco EoX API using the configured settings"
    )

    cisco_eox_api_auto_sync_auto_create_elements = models.BooleanField(
        default=False,
        help_text="When set to true, received product IDs which are not included in the blacklist are automatically "
                  "created"
    )

    cisco_eox_api_auto_sync_queries = models.TextField(
        default="",
        null=False,
        blank=True,
        help_text="queries that should be executed against the EoX API"
    )

    eox_api_blacklist = models.TextField(
        default="",
        null=False,
        blank=True,
        help_text="comma separated list of elements which should not be created during the API import. It is only "
                  "relevant if elements are created automatically."
    )

    # Tasks which should only run once
    eox_api_sync_task_id = models.TextField(
        default="",
        null=True,
        blank=True,
    )

    # Messages for the API credential state
    cisco_api_credentials_successful_tested = models.BooleanField(
        default=False,
        help_text="If credentials are changed in the settings page, it will verify it and write the result to DB"
    )

    cisco_api_credentials_last_message = models.TextField(
        default="not tested",
        help_text="Last (error) message of the Hello API test"
    )

    # Messages for the auto synchronization state
    cisco_eox_api_auto_sync_last_execution_time = models.DateTimeField(
        blank=True,
        null=True,
        help_text="last timestamp when the automatic EoX synchronization was executed"
    )

    cisco_eox_api_auto_sync_last_execution_result = models.TextField(
        default="not executed",
        help_text="Last results of the automatic Cisco EoX synchronization"
    )

    # If set to true, no external requests are sent (just for testing purpose)
    demo_mode = models.BooleanField(
        default=False,
        help_text="If set to true, the application runs in demo mode. Demo mode is used with Testing and will disable "
                  "all periodic tasks"
    )

    def __str__(self):
        return str(self.id)

    def __unicode__(self):
        return str(self.id)


class CiscoApiAuthSettings(models.Model):

    api_client_id = models.TextField(
        default="PlsChgMe",
        null=False,
        blank=True,
        help_text="Client ID for the Cisco API authentication"
    )

    api_client_secret = models.TextField(
        default="PlsChgMe",
        null=False,
        blank=True,
        help_text="Client Secret for the Cisco API authentication"
    )

    cached_http_auth_header = models.TextField(
        default="",
        null=False,
        blank=True,
        help_text="cached authentication header with expire date in JSON format"
    )

# import custom signals for models
import app.productdb.signals
