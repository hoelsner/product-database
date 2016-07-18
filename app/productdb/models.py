from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.timezone import datetime

# choices for the currency
from app.productdb.validators import validate_product_list_string

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
        verbose_name = "vendor"
        verbose_name_plural = "vendors"
        ordering = ('name',)


class ProductGroup(models.Model):
    """
    Product Group
    """
    name = models.CharField(
        max_length=512,
        help_text="Name of the Product Group"
    )

    vendor = models.ForeignKey(
        Vendor,
        blank=False,
        null=False,
        default=0,
        verbose_name="Vendor",
        on_delete=models.SET_DEFAULT
    )

    def get_all_products(self):
        """
        returns a query set that contains all Products
        """
        try:
            result = Product.objects.filter(product_group=self)
            if result.count() == 0:
                result = None

        except:
            # if something went wrong, return None
            result = None

        return result

    def save(self, *args, **kwargs):
        # clean the object before save
        self.clean()
        super(ProductGroup, self).save(*args, **kwargs)

    def clean(self):
        #  the vendor can only be changed if no products are associated to it
        if self.get_all_products():  # not None if no Products are found
            raise ValidationError({
                "vendor": ValidationError("cannot set new vendor as long as there are products associated to ir")
            })

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "product group"
        verbose_name_plural = "product groups"
        unique_together = ("name", "vendor")


class Product(models.Model):
    END_OF_SUPPORT_STR = "End of Support"
    END_OF_SALE_STR = "End of Sale"
    EOS_ANNOUNCED_STR = "EoS announced"
    NO_EOL_ANNOUNCEMENT_STR = "No EoL announcement"

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

    product_group = models.ForeignKey(
        ProductGroup,
        null=True,
        blank=True,
        verbose_name="Product Group",
        on_delete=models.SET_NULL,
        validators=[]
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
                    result.append(self.END_OF_SUPPORT_STR)

                else:
                    result.append(self.END_OF_SALE_STR)
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
                result.append(self.EOS_ANNOUNCED_STR)

            return result

        else:
            if self.eox_update_time_stamp is not None:
                return [self.NO_EOL_ANNOUNCEMENT_STR]
            else:
                return None

    def __str__(self):
        return self.product_id

    def __unicode__(self):
        return self.product_id

    def save(self, *args, **kwargs):
        # clean the object before save
        self.clean()
        super(Product, self).save(*args, **kwargs)

    def clean(self):
        # the vendor values of the product group and the product must be the same
        if self.product_group:
            if self.product_group.vendor != self.vendor:
                raise ValidationError({
                    "product_group":
                        ValidationError(
                            "Invalid product group, group and product must be associated to the same vendor",
                            code='invalid'
                        )
                })

    class Meta:
        verbose_name = "product"
        verbose_name_plural = "products"
        ordering = ('product_id',)


class ProductList(models.Model):
    name = models.CharField(
        max_length=2048,
        unique=True,
        help_text="unique name for the product list",
        verbose_name="Product List Name:"
    )

    string_product_list = models.TextField(
        max_length=16384,
        help_text="Product IDs separated by word wrap or semicolon",
        verbose_name="Unstructured Product ID list:",
        validators=[validate_product_list_string]
    )

    description = models.TextField(
        max_length=4096,
        blank=True,
        null=True,
        verbose_name="Description:",
        help_text="short description what's part of this Product List"
    )

    update_date = models.DateField(
        auto_now=True
    )

    update_user = models.ForeignKey(
        User,
        related_name='product_lists',
        on_delete=models.CASCADE
    )

    def get_string_product_list_as_list(self):
        result = []
        for line in self.string_product_list.splitlines():
            result += line.split(";")
        return sorted([e.strip() for e in result])

    def get_product_list_objects(self):
        q_filter = Q()
        for product_id in self.get_string_product_list_as_list():
            q_filter.add(Q(product_id=product_id), Q.OR)

        return Product.objects.filter(q_filter)

    def save(self, **kwargs):
        self.full_clean()

        # normalize value in database and remove duplicates
        values = self.get_string_product_list_as_list()
        self.string_product_list = "\n".join(list(set(values)))

        super(ProductList, self).save(**kwargs)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "product list"
        verbose_name_plural = "product lists"
        ordering = ('name',)
