from datetime import timedelta

import reversion
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.timezone import datetime

# choices for the currency
CURRENCY_CHOICES = (
    ('EUR', 'Euro'),
    ('USD', 'US-Dollar'),
)


class JobFile(models.Model):
    """
    Uploaded Files
    """
    file = models.FileField(upload_to=settings.DATA_DIRECTORY)


@receiver(pre_delete, sender=JobFile)
def delete_job_file(sender, instance, **kwargs):
    """
    remove the file from the harddisk if the Job File database object is deleted
    """
    instance.file.delete(False)


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
        default="",
        blank=True,
        null=True,
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
        null=True,
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
        verbose_name="EoX lifecycle data timestamp",
        help_text="Indicates that the product has lifecycle data and when they were last updated. If no "
                  "EoL announcement date is set, the product is considered as not EoL/EoS."
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

    eol_reference_number = models.CharField(
        max_length=2048,
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

    @property
    def current_lifecycle_states(self):
        """
        returns a list with all EoL states or None if no EoL announcement ist set
        """
        # compute only if an EoL announcement date is specified
        if self.eol_ext_announcement_date:
            # check the current state
            result = []
            today = datetime.now().date()

            end_of_sale_date = self.end_of_sale_date \
                if self.end_of_sale_date else (datetime.now() + timedelta(days=7)).date()
            end_of_support_date = self.end_of_support_date \
                if self.end_of_support_date else (datetime.now() + timedelta(days=7)).date()
            end_of_new_service_attachment_date = self.end_of_new_service_attachment_date \
                if self.end_of_new_service_attachment_date else (datetime.now() + timedelta(days=7)).date()
            end_of_sw_maintenance_date = self.end_of_sw_maintenance_date \
                if self.end_of_sw_maintenance_date else (datetime.now() + timedelta(days=7)).date()
            end_of_routine_failure_analysis = self.end_of_routine_failure_analysis \
                if self.end_of_routine_failure_analysis else (datetime.now() + timedelta(days=7)).date()
            end_of_service_contract_renewal = self.end_of_service_contract_renewal \
                if self.end_of_service_contract_renewal else (datetime.now() + timedelta(days=7)).date()
            end_of_sec_vuln_supp_date = self.end_of_sec_vuln_supp_date \
                if self.end_of_sec_vuln_supp_date else (datetime.now() + timedelta(days=7)).date()

            if today > end_of_sale_date:
                if today > end_of_support_date:
                    result.append("End of Support")

                else:
                    result.append("End of Sale")
                    if today > end_of_new_service_attachment_date:
                        result.append("End of New Service Attachment Date")

                    if today > end_of_sw_maintenance_date:
                        result.append("End of SW Maintenance Releases Date")

                    if today > end_of_routine_failure_analysis:
                        result.append("End of Routine Failure Analysis Date")

                    if today > end_of_service_contract_renewal:
                        result.append("End of Service Contract Renewal Date")

                    if today > end_of_sec_vuln_supp_date:
                        result.append("End of Vulnerability/Security Support date")

            else:
                # product is eos announced
                result.append("EoS announced")

            return result

        else:
            if self.eox_update_time_stamp is not None:
                return ["No EoL announcement"]
            else:
                return None

    def __str__(self):
        return self.product_id

    def __unicode__(self):
        return self.product_id

    class Meta:
        ordering = ('product_id',)
