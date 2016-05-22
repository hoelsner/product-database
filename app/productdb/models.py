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
    product_id = models.CharField(
        unique=True,
        max_length=512,
        help_text="Unique Product ID/Number"
    )

    description = models.TextField(
        default="not set",
        help_text="description"
    )

    list_price = models.DecimalField(
        null=True,
        blank=True,
        decimal_places=2,
        max_digits=32,
        verbose_name="list price",
        help_text="list price of the element",
        validators=[MinValueValidator(0)]
    )

    currency = models.CharField(
        max_length=16,
        choices=CURRENCY_CHOICES,
        default="USD",
        verbose_name="currency",
        help_text="currency of the list price"
    )

    tags = models.TextField(
        default="",
        blank=True,
        verbose_name="Tags",
        help_text="unformatted tag field"
    )

    vendor = models.ForeignKey(
        Vendor,
        blank=False,
        null=False,
        default=0,
        verbose_name="Vendor",
        on_delete=models.SET_DEFAULT
    )

    eox_update_time_stamp = models.DateField(
        null=True,
        blank=True,
        verbose_name="EoX lifecycle data timestamp"
    )

    eol_ext_announcement_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="End-of-Life Announcement Date"
    )

    end_of_sale_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="End-of-Sale Date"
    )

    end_of_new_service_attachment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="End of New Service Attachment Date"
    )

    end_of_sw_maintenance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="End of SW Maintenance Releases Date"
    )

    end_of_routine_failure_analysis = models.DateField(
        null=True,
        blank=True,
        verbose_name="End of Routine Failure Analysis Date"
    )

    end_of_service_contract_renewal = models.DateField(
        null=True,
        blank=True,
        verbose_name="End of Service Contract Renewal Date"
    )

    end_of_support_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Last Date of Support",
    )

    end_of_sec_vuln_supp_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="End of Vulnerability/Security Support date"
    )

    eol_reference_number = models.TextField(
        null=True,
        blank=True,
        verbose_name="EoL reference number",
        help_text="Product bulletin number or vendor specific reference for EoL"
    )

    eol_reference_url = models.URLField(
        null=True,
        blank=True,
        verbose_name="EoL reference URL",
        help_text="URL to the Product bulletin or EoL reference"
    )

    def __str__(self):
        return self.product_id

    def __unicode__(self):
        return self.product_id

    class Meta:
        ordering = ('product_id',)
