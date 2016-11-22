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
from django.db.models.signals import pre_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils.timezone import datetime
from app.productdb.validators import validate_product_list_string

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
        result = Product.objects.filter(product_group=self)
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
        verbose_name = "product group"
        verbose_name_plural = "product groups"
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

    def __str__(self):
        return self.product_id

    def save(self, *args, **kwargs):
        # strip URL value
        if self.eol_reference_url is not None:
            self.eol_reference_url = self.eol_reference_url.strip()

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

    def get_preferred_replacement_option(self):
        if self.has_migration_options():
            return self.get_migration_path(self.productmigrationoption_set.first().migration_source.name)[-1]
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
                # use the preferred path
                migration_source_name = self.productmigrationoption_set.all().first().migration_source.name

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
        verbose_name = "product"
        verbose_name_plural = "products"
        ordering = ('product_id',)


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
        verbose_name = "product migration source"
        verbose_name_plural = "product migration sources"
        ordering = ["-preference", "name"]  # sort descending, that the most preferred source is always on op


class ProductMigrationOption(models.Model):
    product = models.ForeignKey(Product)
    migration_source = models.ForeignKey(ProductMigrationSource)

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

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.full_clean()
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return "replacement option for %s" % self.product.product_id

    class Meta:
        # only a single migration option is allowed per migration source
        unique_together = ["product", "migration_source"]
        ordering = ["-migration_source__preference"]  # first element is from the source that is most preferred
        verbose_name = "product migration option"
        verbose_name_plural = "product migration options"


class ProductList(models.Model):
    name = models.CharField(
        max_length=2048,
        unique=True,
        help_text="unique name for the product list",
        verbose_name="Product List Name"
    )

    string_product_list = models.TextField(
        max_length=16384,
        help_text="Product IDs separated by word wrap or semicolon",
        verbose_name="Unstructured Product IDs separated by line break",
        validators=[validate_product_list_string]
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

    def get_string_product_list_as_list(self):
        result = []
        for line in self.string_product_list.splitlines():
            result += line.split(";")
        return sorted([e.strip() for e in result])

    def get_product_list_objects(self):
        q_filter = Q()
        for product_id in self.get_string_product_list_as_list():
            q_filter.add(Q(product_id=product_id), Q.OR)

        return Product.objects.filter(q_filter).prefetch_related("vendor", "product_group")

    def save(self, **kwargs):
        self.full_clean()

        # normalize value in database, remove duplicates and sort the list
        values = self.get_string_product_list_as_list()
        self.string_product_list = "\n".join(sorted(list(set(values))))

        super(ProductList, self).save(**kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "product list"
        verbose_name_plural = "product lists"
        ordering = ('name',)


class UserProfileManager(models.Manager):
    def get_by_natural_key(self, username):
        return self.get(user=User.objects.get(username=username))


class UserProfile(models.Model):
    objects = UserProfileManager()
    user = models.OneToOneField(User, related_name='profile', unique=True)

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
        verbose_name="use regex search",
        help_text="Use regular expression in any search field (fallback to simple search if no valid "
                  "regular expression is used)"
    )

    def natural_key(self):
        return self.user.username

    def __str__(self):
        return "User Profile for %s" % self.user.username


@receiver(post_save, sender=User)
def create_user_profile_if_not_exist(sender, instance, **kwargs):
    if not UserProfile.objects.filter(user=instance).exists():
        # create new user profile with default options
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=ProductList)
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


@receiver(post_save, sender=Product)
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
