from django.core.validators import MinValueValidator
from django.db import models

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

    def delete(self, using=None, **kwargs):
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
