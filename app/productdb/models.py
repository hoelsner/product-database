import hashlib
import re
from collections import Counter
from datetime import timedelta
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_delete, post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import datetime, now
from app.config.settings import AppSettings
from app.productdb.validators import validate_product_list_string
from app.productdb import utils

CURRENCY_CHOICES = (
    ('EUR', 'Euro'),
    ('USD', 'US-Dollar'),
)


class JobFile(models.Model):
    """Uploaded files for tasks"""
    file = models.FileField(upload_to=settings.DATA_DIRECTORY)


@receiver(pre_delete, sender=JobFile)
def delete_job_file(sender, instance, **kwargs):
    """remove the file from the disk if the Job File object is deleted"""
    instance.file.delete(False)


class Vendor(models.Model):
    """
    Vendor
    """
    name = models.CharField(
        max_length=128,
        unique=True
    )

    def __str__(self):
        return self.name

    def delete(self, using=None, **kwargs):
        # prevent the deletion of the "unassigned" value from model
        if self.id == 0:
            raise Exception("Operation not allowed")
        super().delete(using)

    def save(self, **kwargs):
        # clean the object before save
        self.full_clean()
        super(Vendor, self).save(**kwargs)

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
        """returns a query set that contains all Products"""
        result = None
        if self.pk:
            result = Product.objects.filter(product_group_id=self.pk)
            if result.count() == 0:
                result = None

        return result

    def save(self, *args, **kwargs):
        # clean the object before save
        self.full_clean()
        super(ProductGroup, self).save(*args, **kwargs)

    def clean(self):
        # check that the Product Group Name already exist in the database for the given vendor
        if ProductGroup.objects.filter(vendor=self.vendor, name=self.name).exists():
            raise ValidationError({
                "name": ValidationError("group name already defined for this vendor")
            })

        # verify that all associated Products have the same Vendor as the product list
        associated_products = self.get_all_products()
        import logging
        logging.debug("Associated Products to %s: %s - %s" %(
            self.name,
            len(associated_products) if associated_products is not None else "0 (None)",
            associated_products.values_list("product_id", flat=True) if associated_products is not None else "[]"
        ))

        # if no products are associated to the group, no check is required
        if associated_products:
            products_with_different_vendor = [False for product in self.get_all_products()
                                              if product.vendor != self.vendor]
            if len(products_with_different_vendor) != 0:
                raise ValidationError({
                    "vendor": ValidationError("cannot set new vendor as long as there are products associated to it")
                })

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product Group"
        verbose_name_plural = "Product Groups"
        unique_together = ("name", "vendor")


class Product(models.Model):
    END_OF_SUPPORT_STR = "End of Support"
    END_OF_SALE_STR = "End of Sale"
    END_OF_NEW_SERVICE_ATTACHMENT_STR = "End of New Service Attachment Date"
    END_OF_SW_MAINTENANCE_RELEASES_STR = "End of SW Maintenance Releases Date"
    END_OF_ROUTINE_FAILURE_ANALYSIS_STR = "End of Routine Failure Analysis Date"
    END_OF_SERVICE_CONTRACT_RENEWAL_STR = "End of Service Contract Renewal Date"
    END_OF_VUL_SUPPORT_STR = "End of Vulnerability/Security Support date"
    EOS_ANNOUNCED_STR = "EoS announced"
    NO_EOL_ANNOUNCEMENT_STR = "No EoL announcement"

    # preference greater than the following constant is considered preferred
    LESS_PREFERRED_PREFERENCE_VALUE = 25

    product_id = models.CharField(
        unique=False,
        max_length=512,
        help_text="Product ID/Number"
    )

    description = models.TextField(
        default="",
        blank=True,
        null=True,
        help_text="description of the product"
    )

    list_price = models.FloatField(
        null=True,
        blank=True,
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
        help_text="unstructured tag field"
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
        help_text="Indicates that the product has lifecycle data and when they were updated. If no "
                  "EoL announcement date is set but an update timestamp, the product is considered as not EoL/EoS."
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
        max_length=1024,
        verbose_name="EoL reference URL",
        help_text="URL to the Product bulletin or EoL reference"
    )

    product_group = models.ForeignKey(
        ProductGroup,
        null=True,
        blank=True,
        verbose_name="Product Group",
        on_delete=models.SET_NULL
    )

    lc_state_sync = models.BooleanField(
        default=False,
        verbose_name="lifecycle data automatically synchronized",
        help_text="product is automatically synchronized against the vendor data"  # always false except for Cisco EoX
                                                                                   # API entries
    )

    internal_product_id = models.CharField(
        verbose_name="Internal Product ID",
        help_text="optional internal reference for the Product",
        max_length=255,
        null=True,
        blank=True
    )

    update_timestamp = models.DateField(
        verbose_name="update timestamp",
        help_text="last changes to the product data",
        auto_created=True,
        default=now
    )

    list_price_timestamp = models.DateField(
        verbose_name="list price timestamp",
        help_text="last change of the list price",
        null=True,
        blank=True
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

            # if not defined, use a date in the future
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

            if today >= end_of_sale_date:
                if today >= end_of_support_date:
                    result.append(self.END_OF_SUPPORT_STR)

                else:
                    result.append(self.END_OF_SALE_STR)
                    if today >= end_of_new_service_attachment_date:
                        result.append(self.END_OF_NEW_SERVICE_ATTACHMENT_STR)

                    if today >= end_of_sw_maintenance_date:
                        result.append(self.END_OF_SW_MAINTENANCE_RELEASES_STR)

                    if today >= end_of_routine_failure_analysis:
                        result.append(self.END_OF_ROUTINE_FAILURE_ANALYSIS_STR)

                    if today >= end_of_service_contract_renewal:
                        result.append(self.END_OF_SERVICE_CONTRACT_RENEWAL_STR)

                    if today >= end_of_sec_vuln_supp_date:
                        result.append(self.END_OF_VUL_SUPPORT_STR)

            else:
                # product is eos announced
                result.append(self.EOS_ANNOUNCED_STR)

            return result

        else:
            if self.eox_update_time_stamp is not None:
                return [self.NO_EOL_ANNOUNCEMENT_STR]

            else:
                return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__loaded_list_price = self.list_price
        self.__loaded_lc_state_sync = self.lc_state_sync

    def __str__(self):
        return self.product_id

    def save(self, *args, **kwargs):
        # strip URL value
        if self.eol_reference_url is not None:
            self.eol_reference_url = self.eol_reference_url.strip()

        if self.__loaded_list_price != self.list_price:
            # price has changed, update flag
            self.list_price_timestamp = datetime.today()

        # the state sync is only updated within a separate task and always updated separately
        if self.__loaded_lc_state_sync == self.lc_state_sync:
            # state sync not changed, update of the update timestamp
            self.update_timestamp = datetime.today()

        # clean the object before save
        self.full_clean()
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

    def has_migration_options(self):
        return self.productmigrationoption_set.exists()

    def has_preferred_migration_option(self):
        """check that a preferred migration option exist (Product Migration Source preference > 25)"""
        return self.productmigrationoption_set.filter(
            migration_source__preference__gt=self.LESS_PREFERRED_PREFERENCE_VALUE
        ).count() != 0

    def get_preferred_replacement_option(self):
        """Return the preferred replacement option (Product Migration Sources with a preference greater than 25)"""
        if self.has_migration_options() and self.has_preferred_migration_option():
            return self.get_migration_path(self.productmigrationoption_set.filter(
                migration_source__preference__gt=self.LESS_PREFERRED_PREFERENCE_VALUE
            ).first().migration_source.name)[-1]
        return None

    def get_migration_path(self, migration_source_name=None):
        """
        recursive lookup of the given migration source name, result is an ordered list, the first element
        is the direct replacement and the last one is the valid replacement
        """
        if not migration_source_name:
            if not self.productmigrationoption_set.all().exists():
                return []

            else:
                # use the preferred path (except all Migration sources with a preference of 25 and lower)
                migration_source_name = self.productmigrationoption_set.filter(
                    migration_source__preference__gt=self.LESS_PREFERRED_PREFERENCE_VALUE
                ).first().migration_source.name

        if type(migration_source_name) is not str:
            raise AttributeError("attribute 'migration_source_name' must be a string")

        result = []
        if self.productmigrationoption_set.filter(migration_source__name=migration_source_name).exists():
            result.append(self.productmigrationoption_set.filter(migration_source__name=migration_source_name).first())

            while True:
                # test, that the product migration option is valid and that a replacement_product_id exists
                if not result[-1].is_valid_replacement() and result[-1].replacement_product_id:
                    # test if it is in the database
                    if result[-1].is_replacement_in_db():
                        # get replacement product ID from database
                        p = Product.objects.get(product_id=result[-1].replacement_product_id)
                        if p.productmigrationoption_set.filter(migration_source__name=migration_source_name).exists():
                            result.append(
                                p.productmigrationoption_set.filter(
                                    migration_source__name=migration_source_name
                                )[:1].first()
                            )
                        else:
                            break
                    else:
                        break
                else:
                    break

        return result

    def get_product_migration_source_names_set(self):
        return list(self.productmigrationoption_set.all().values_list("migration_source__name", flat=True))

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        unique_together = ("product_id", "vendor",)
        ordering = ("product_id",)


class ProductMigrationSource(models.Model):
    name = models.CharField(
        help_text="name of the migration source",
        unique=True,
        max_length=255
    )

    description = models.TextField(
        help_text="",
        max_length=4096,
        blank=True,
        null=True
    )

    preference = models.PositiveSmallIntegerField(
        help_text="preference value, identifies which source is preferred over another (100 is most preferred)",
        validators=[
            MaxValueValidator(100),
            MinValueValidator(1)
        ],
        default=50
    )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product Migration Source"
        verbose_name_plural = "Product Migration Sources"
        ordering = ["-preference", "name"]  # sort descending, that the most preferred source is always on op


class ProductMigrationOption(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    migration_source = models.ForeignKey(ProductMigrationSource, on_delete=models.CASCADE)

    replacement_product_id = models.CharField(
        max_length=512,
        help_text="the suggested replacement option",
        null=False,
        blank=True
    )
    replacement_db_product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="replacement_db_product"
    )
    comment = models.TextField(
        max_length=4096,
        help_text="comment from the group (optional)",
        null=False,
        blank=True
    )

    migration_product_info_url = models.URLField(
        null=True,
        blank=True,
        verbose_name="Migration Product Info URL",
        help_text="Migration Product Information URL"
    )

    def is_replacement_in_db(self):
        """True, if the replacement product exists in the database"""
        return self.replacement_db_product is not None

    def get_product_replacement_id(self):
        """returns the product ID of the replacement, if not defined or not in the database, result is None"""
        return self.replacement_db_product.id if self.replacement_db_product else None

    def is_valid_replacement(self):
        """Check that the object is a valid replacement option. A replacement option is valid if
         * a replacement Product ID is set and not part of the database
         * a replacement Product ID is set and part of the database (only, if the Product is not EoL announced)
        """
        if self.replacement_product_id:
            if self.is_replacement_in_db():
                # replacement product ID is part of the database
                if not self.replacement_db_product.end_of_sale_date or \
                                self.replacement_db_product.current_lifecycle_states == [Product.NO_EOL_ANNOUNCEMENT_STR]:
                    # product is not EoL and therefore valid
                    return True

                else:
                    return False

            else:
                return True

        return False

    def get_valid_replacement_product(self):
        """get a valid replacement product for this migration source"""
        if self.is_valid_replacement():
            return self.replacement_db_product

        return None

    def clean(self):
        # check required to get a proper validation working within the Django admin (unique together with the required
        # FK values)
        if self.product_id is not None and self.migration_source_id is not None:
            # validate that this combination does not already exist (issue when using django admin)
            qs = ProductMigrationOption.objects.exclude(pk=self.pk).filter(
                product__id=self.product_id,
                migration_source__id=self.migration_source_id
            )
            if qs.count() > 0:
                # one of the fields must be changed, therefore view the error on both attributes
                msg = "Product Migration Option with this Product ID and Migration Source already exists"
                raise ValidationError({"product_id": msg, "migration_source": msg})

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return "replacement option for %s" % self.product.product_id

    class Meta:
        # only a single migration option is allowed per migration source
        unique_together = ["product", "migration_source"]
        ordering = ["-migration_source__preference"]  # first element is from the source that is most preferred
        verbose_name = "Product Migration Option"
        verbose_name_plural = "Product Migration Options"


class ProductList(models.Model):
    name = models.CharField(
        max_length=2048,
        unique=True,
        help_text="unique name for the product list",
        verbose_name="Product List Name"
    )

    vendor = models.ForeignKey(
        Vendor,
        help_text="vendor for the product list (only products from a single vendor can be used within a product list)",
        verbose_name="Vendor",
        on_delete=models.CASCADE,
        # auto-discovery based on the list entries is implemented as part of the save function
        # required only for data migration
        null=True,
        blank=False
    )

    string_product_list = models.TextField(
        help_text="Product IDs separated by word wrap or semicolon",
        verbose_name="Unstructured Product IDs separated by line break"
    )

    description = models.TextField(
        max_length=4096,
        blank=True,
        null=False,
        verbose_name="Description",
        help_text="short description what's part of this Product List (markdown and/or HTML)"
    )

    version_note = models.TextField(
        max_length=16384,
        blank=True,
        null=False,
        verbose_name="Version note",
        help_text="some version information for the product list (markdown and/or HTML)"
    )

    update_date = models.DateField(
        auto_now=True
    )

    update_user = models.ForeignKey(
        User,
        related_name='product_lists',
        on_delete=models.CASCADE
    )

    hash = models.CharField(
        max_length=64,
        null=False,
        blank=True,
        default=""
    )

    def get_string_product_list_as_list(self):
        result = []
        for line in self.string_product_list.splitlines():
            result += line.split(";")
        return sorted([e.strip() for e in result])

    def get_product_list_objects(self):
        q_filter = Q()
        for product_id in self.get_string_product_list_as_list():
            q_filter.add(Q(product_id=product_id, vendor_id=self.vendor_id), Q.OR)

        return Product.objects.filter(q_filter).prefetch_related("vendor", "product_group")

    def full_clean(self, exclude=None, validate_unique=True):
        # validate product list string together with selected vendor
        result = super().full_clean(exclude, validate_unique)
        # validation between fields
        self.__discover_vendor_based_on_products()
        if self.vendor is not None:
            validate_product_list_string(self.string_product_list, self.vendor.id)

        else:
            raise ValidationError("vendor not set")

        return result

    def save(self, **kwargs):
        self.__discover_vendor_based_on_products()
        self.full_clean()

        # normalize value in database, remove duplicates and sort the list
        values = self.get_string_product_list_as_list()
        self.string_product_list = "\n".join(sorted(list(set(values))))

        # calculate hash value for Product check linking on the queries
        s = "%s:%s:%s" % (self.name, self.string_product_list, self.vendor_id)
        self.hash = hashlib.sha256(s.encode()).hexdigest()

        super(ProductList, self).save(**kwargs)

    def __discover_vendor_based_on_products(self):
        # discovery vendor based on the products (if not set, used primary for data migration)
        if self.vendor is None:
            product_id_list = self.get_string_product_list_as_list()
            if len(product_id_list) > 0:
                self.vendor = Product.objects.filter(product_id=product_id_list[-1]).first().vendor

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product List"
        verbose_name_plural = "Product Lists"
        ordering = ('name',)


class UserProfileManager(models.Manager):
    def get_by_natural_key(self, username):
        return self.get(user=User.objects.get(username=username))


class UserProfile(models.Model):
    objects = UserProfileManager()
    user = models.OneToOneField(
        User,
        related_name='profile',
        on_delete=models.CASCADE,
        unique=True
    )

    preferred_vendor = models.ForeignKey(
        Vendor,
        blank=False,
        null=False,
        default=1,
        verbose_name="preferred vendor",
        help_text="vendor that is selected by default in all vendor specific views",
        on_delete=models.SET_DEFAULT
    )

    regex_search = models.BooleanField(
        default=False,
        verbose_name="use regular expressions in search fields",
        help_text="Use regular expression in any search field (fallback to simple search if no valid "
                  "regular expression is used)"
    )

    choose_migration_source = models.BooleanField(
        default=False,
        verbose_name="choose Migration Source in Product Check",
        help_text="specify the Migration Source for a Product Check (don't use the preferred migration path)"
    )

    def natural_key(self):
        return self.user.username

    def __str__(self):
        return "User Profile for %s" % self.user.username


class ProductCheckInputChunks(models.Model):
    """chunks for the input product IDs field in the product check"""
    sequence = models.PositiveIntegerField()

    input_product_ids_chunk = models.CharField(
        max_length=65536,
        null=False,
        blank=True
    )

    product_check = models.ForeignKey(
        "ProductCheck",
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['sequence']


class ProductCheck(models.Model):
    name = models.CharField(
        verbose_name="Name",
        help_text="Name to identify the Product Check",
        max_length=256
    )

    migration_source = models.ForeignKey(
        ProductMigrationSource,
        verbose_name="migration source",
        help_text="migration source to identify the replacement options, if not selected the preferred migration path "
                  "is used",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    @property
    def use_preferred_migration_source(self):
        """if no migration source is choosen, always use the preferred one"""
        return self.migration_source is None

    # buffer value (before save)
    _input_product_ids = ""

    @property
    def input_product_ids(self):
        """return concat string of all input product id chunks"""
        if self._input_product_ids == "":
            values = self.productcheckinputchunks_set.values_list("input_product_ids_chunk", flat=True)
            return "".join(values)

        else:
            return self._input_product_ids

    @input_product_ids.setter
    def input_product_ids(self, value):
        if type(value) is not str:
            raise AttributeError("value must be a string type")

        self._input_product_ids = value

    @property
    def input_product_ids_list(self):
        result = []
        for line in [line.strip() for line in self.input_product_ids.splitlines() if line.strip() != ""]:
            result += line.split(";")
        return sorted([e.strip() for e in result])

    last_change = models.DateTimeField(
        auto_now=True
    )

    create_user = models.ForeignKey(
        User,
        help_text="if not null, the product check is available to all users",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    @property
    def is_public(self):
        return self.create_user is None

    task_id = models.CharField(
        help_text="if set, the product check is currently executed",
        max_length=64,
        null=True,
        blank=True
    )

    @property
    def in_progress(self):
        """product check is currently processed"""
        return self.task_id is not None

    def perform_product_check(self):
        """perform the product check and populate the ProductCheckEntries"""
        unique_products = [line.strip() for line in set(self.input_product_ids_list) if line.strip() != ""]
        amounts = Counter(self.input_product_ids_list)

        # clean all entries
        self.productcheckentry_set.all().delete()

        for input_product_id in unique_products:
            product_entry, _ = ProductCheckEntry.objects.get_or_create(
                input_product_id=input_product_id,
                product_check=self
            )
            product_entry.amount = amounts[input_product_id]
            product_entry.discover_product_list_values()

            product_entry.save()

        # increments statistics
        settings = AppSettings()
        settings.set_amount_of_product_checks(settings.get_amount_of_product_checks() + 1)
        settings.set_amount_of_unique_product_check_entries(settings.get_amount_of_unique_product_check_entries() +
                                                            len(unique_products))

        self.save()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        super().save(force_insert, force_update, using, update_fields)

        # save chunks to database (if new value is set)
        if self._input_product_ids != "":
            self.productcheckinputchunks_set.all().delete()

            chunks = utils.split_string(self._input_product_ids, 65536)
            counter = 1
            for chunk in chunks:
                ProductCheckInputChunks.objects.create(product_check=self, input_product_ids_chunk=chunk, sequence=counter)
                counter += 1

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Class 'ProductCheck' %d> %s" % (self.id, self.name)

    class Meta:
        verbose_name = "Product Check"
        verbose_name_plural = "Product Checks"


class ProductCheckEntry(models.Model):
    product_check = models.ForeignKey(
        ProductCheck,
        on_delete=models.CASCADE
    )

    input_product_id = models.CharField(
        verbose_name="Product ID",
        max_length=256
    )

    product_in_database = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    @property
    def in_database(self):
        return self.product_in_database is not None

    amount = models.PositiveIntegerField(
        verbose_name="amount",
        default=0
    )

    migration_product = models.ForeignKey(
        ProductMigrationOption,
        verbose_name="Migration Option",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    part_of_product_list = models.TextField(
        verbose_name="product list hash values",
        help_text="hash values of product lists that contain the Product (at time of the check)",
        max_length=8192,
        null=False,
        blank=True,
        default=""
    )

    @property
    def product_list_hash_values(self):
        """return an unordered list of hash strings that contains the Product at time of the check"""
        return self.part_of_product_list.splitlines()

    def get_product_list_names(self):
        """return an list of Product List Names that contains the Product at time of the check"""
        self.__discover_product_relation_in_database()
        return ProductList.objects.filter(hash__in=self.product_list_hash_values).values_list("name", flat=True)

    def discover_product_list_values(self):
        """populate the part_of_product_list field"""
        self.part_of_product_list = ""
        query = ProductList.objects.filter(string_product_list__contains=self.input_product_id)
        self.part_of_product_list += "\n".join(query.values_list("hash", flat=True))

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        self.__discover_product_relation_in_database(force_update=True)
        super().save(force_insert, force_update, using, update_fields)

    def __discover_product_relation_in_database(self, force_update=False):
        """populate the 'product_in_database' relation as a shortcut if possible"""
        if (self.product_in_database is None) or (force_update is False):
            query = Product.objects.filter(product_id=self.input_product_id)
            if query.count() != 0:
                self.product_in_database = query.first()

                if self.product_check.migration_source:
                    # if the product check defines a migration source, try a lookup on this verison
                    replacement_product_list = self.product_in_database.get_migration_path(self.product_check.migration_source.name)
                    if len(replacement_product_list) != 0:
                        self.migration_product = replacement_product_list[-1]

                else:
                    # if nothing is specified, get the preferred replacement option
                    self.migration_product = self.product_in_database.get_preferred_replacement_option()

    def __str__(self):
        return "%s: %s (%d)" % (self.product_check, self.input_product_id, self.amount)

    def __repr__(self):
        return "<Class 'ProductCheckEntry' %d> %s (ProductCheck '%d')" % (self.id, self.input_product_id, self.product_check_id)

    class Meta:
        verbose_name = "Product Check Entry"
        verbose_name_plural = "Product Check Entries"


class ProductIdNormalizationRule(models.Model):
    """
    Normalization rule for a Product ID
    """
    vendor = models.ForeignKey(
        Vendor,
        verbose_name="Vendor",
        help_text="Vendor where the rule should apply",
        on_delete=models.CASCADE
    )

    product_id = models.CharField(
        verbose_name="Product ID",
        help_text="Normalized Product ID that should be used",
        max_length=255,
        null=True,
        blank=True
    )

    regex_match = models.CharField(
        verbose_name="RegEx to Match",
        help_text="Condition for a given input to match the Product ID",
        max_length=255,
        null=True,
        blank=True
    )

    comment = models.CharField(
        verbose_name="Comment",
        help_text="Rule comment",
        max_length=4096,
        null=True,
        blank=True
    )

    priority = models.IntegerField(
        verbose_name="Priority",
        help_text="priority of the rule",
        default=500
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pattern = None

    def matches(self, raw_product_id):
        """
        returns True if the given Product ID matches the pattern from the instance
        :param raw_product_id: raw Product ID
        :return:
        """
        if self._pattern is None:
            self._pattern = re.compile(self.regex_match)

        if self._pattern.match(raw_product_id):
            return True

        else:
            return False

    def get_normalized_product_id(self, raw_product_id):
        """
        get the normalization result of a given raw_product_id
        :raises AttributeError: if the raw_product_id doesn't match this entry
        :param raw_product_id:
        :return:
        """
        if not self.matches(raw_product_id):
            raise AttributeError("input product ID does not match normalization")

        if self._pattern.match(raw_product_id):
            groups = self._pattern.match(raw_product_id).groups()
            if len(groups) != 0:
                return self.product_id % groups

        return self.product_id

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        super().save(force_insert, force_update, using, update_fields)

    class Meta:
        verbose_name = "Product ID Normalization Rule"
        verbose_name_plural = "Product ID Normalization Rules"
        ordering = [
            "priority",
            "product_id"
        ]
        unique_together = (
            "vendor",
            "product_id",
            "regex_match"
        )


@receiver(post_save, sender=User)
def create_user_profile_if_not_exist(sender, instance, **kwargs):
    if not UserProfile.objects.filter(user=instance).exists():
        # create new user profile with default options
        UserProfile.objects.create(user=instance)


@receiver([post_save, post_delete], sender=ProductList)
def invalidate_page_cache(sender, instance, **kwargs):
    key = make_template_fragment_key("productlist_detail", [instance.id, False])
    if key:
        cache.delete(key)
    key = make_template_fragment_key("productlist_detail", [instance.id, True])
    if key:
        cache.delete(key)


@receiver(post_save, sender=Product)
def update_db_state_for_the_migration_options_with_product_id(sender, instance, **kwargs):
    """save all Product Migration Options where the replacement product ID is the same as the Product ID that was
    saved to update the replacement_in_db flag"""
    for pmo in ProductMigrationOption.objects.filter(replacement_product_id=instance.product_id):
        pmo.save()


@receiver([post_save, post_delete], sender=Product)
def invalidate_product_related_cache_values(sender, instance, **kwargs):
    """delete cache values that are somehow related to the Product data model"""
    cache.delete("PDB_HOMEPAGE_CONTEXT")


@receiver(pre_save, sender=ProductMigrationOption)
def update_product_migration_replacement_id_relation_field(sender, instance, **kwargs):
    """ensures that a database relation for a replacement product ID exists, if the replacement_product_id is part of
    the database, validates that these two values cannot be the same"""
    try:
        # check that the replacement product id is not the same as the original product id (would create a loop
        # within migration path computation)
        if instance.replacement_product_id != instance.product.product_id:
            instance.replacement_db_product = Product.objects.get(product_id=instance.replacement_product_id)

        else:
            raise ValidationError({
                "replacement_product_id": "Product ID that should be replaced cannot be the same as the suggested "
                                          "replacement Product ID"
            })

    except ValidationError:
        raise  # propagate to the save method

    except Exception:
        instance.replacement_db_product = None
