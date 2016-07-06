from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils.datetime_safe import datetime

from app.productdb.models import Vendor, Product, ProductGroup


class VendorDataModelTest(TestCase):
    fixtures = ['default_vendors.yaml']

    def test_delete_fail_for_default_value(self):
        """
        This test ensures, that the value "unassigned" cannot be deleted
        :return:
        """
        try:
            Vendor.objects.get(id=0).delete()
            self.fail("Exception not thrown, delete possible but it should not")

        except Exception as ex:
            self.assertEquals("Operation not allowed", str(ex))

    def test_delete_pass_for_vendor_default_value(self):
        """
        This test ensures, that any other vendor can be deleted
        :return:
        """
        try:
            Vendor.objects.get(id=1).delete()

        except Exception:
            self.fail("Exception thrown, delete not possible but it should")

    def test_verify_string_conversion(self):
        v = Vendor.objects.get(id=1)
        self.assertEquals("Cisco Systems", str(v))
        self.assertEquals("Cisco Systems", v.__unicode__())


class ProductGroupDataModelTest(TestCase):
    fixtures = ["default_vendors.yaml"]

    def test_create_product_group(self):
        """
        create a product group with some elements
        """
        pg1 = ProductGroup.objects.create(name="MyProductGroup")
        unassigned_vendor = Vendor.objects.get(id=0)

        self.assertEqual(pg1.vendor, unassigned_vendor)  # by default the "unassigned" data object is used

        products_dictlist = [
            {
                "product_id": "MyProductId" + str(i),
                "vendor": unassigned_vendor,
                "product_group": pg1
             } for i in range(1, 5)
        ]
        for p in products_dictlist:
            Product.objects.create(**p)

        self.assertEqual(Product.objects.all().count(), pg1.get_all_products().count())

        # adding a Product of a different Vendor will raise a ValidationError when try to save the model
        inv_product = Product.objects.create(product_id="invalid_vendor", vendor=Vendor.objects.get(id=1))
        inv_product.product_group = pg1
        with self.assertRaises(ValidationError):
            inv_product.save()

        self.assertEqual(Product.objects.all().count() - 1, pg1.get_all_products().count())

    def test_unique_together_constraint(self):
        """
        test, that a product group with the same name can be created for multiple vendors, but not within the same vendor
        """
        v1 = Vendor.objects.get(id=1)
        v2 = Vendor.objects.get(id=2)
        _ = ProductGroup.objects.create(name="test", vendor=v1)
        _ = ProductGroup.objects.create(name="test", vendor=v2)

        # the following expression with result in an IntegrityError
        with self.assertRaises(IntegrityError):
            _ = ProductGroup.objects.create(name="test", vendor=v1)

    def test_change_vendor_to_another_vendor_than_the_associated_products(self):
        """
        The change of the vendor as long as there are products associated to it should not be possible
        """
        v1 = Vendor.objects.get(id=1)
        v2 = Vendor.objects.get(id=2)
        pg = ProductGroup.objects.create(name="test", vendor=v1)
        p1 = Product.objects.create(product_id="test product 1", vendor=v1, product_group=pg)

        # error while assigning product group
        with self.assertRaises(ValidationError):
            pg.vendor = v2
            pg.save()

        # remove products from the product list
        p1.product_group = None
        p1.save()

        # set new vendor on the product group (now it works)
        pg.vendor = v2
        pg.save()


class ProductDataModelTest(TestCase):
    fixtures = ['default_vendors.yaml']

    def test_verify_string_conversion(self):
        product_id = "TestProduct"
        p = Product.objects.create(product_id=product_id)
        self.assertEquals(product_id, str(p))
        self.assertEquals(product_id, p.__unicode__())

    def test_current_lifecycle_state(self):
        product_id = "TestProduct"
        p = Product.objects.create(product_id=product_id)
        self.assertEquals(product_id, str(p))
        p.save()

        self.assertIsNone(p.current_lifecycle_states)

        # set an EoX Update timestamp, to indicate that there are valid data in the database
        p.eox_update_time_stamp = datetime.now().date() - timedelta(days=1)

        self.assertIsNotNone(p.current_lifecycle_states)
        self.assertTrue(len(p.current_lifecycle_states) == 1)
        self.assertEqual("No EoL announcement", p.current_lifecycle_states[0])

        # set an EoL announcement date of yesterday
        p.eol_ext_announcement_date = datetime.now().date() - timedelta(days=1)

        self.assertIsNotNone(p.current_lifecycle_states)
        self.assertTrue(len(p.current_lifecycle_states) == 1)
        self.assertEqual("EoS announced", p.current_lifecycle_states[0])

        # set an End of sale date of yesterday
        p.end_of_sale_date = datetime.now().date() - timedelta(days=1)

        self.assertIsNotNone(p.current_lifecycle_states)
        self.assertTrue(len(p.current_lifecycle_states) == 1)
        self.assertEqual("End of Sale", p.current_lifecycle_states[0])

        # set an end_of_new_service_attachment_date date
        p.end_of_new_service_attachment_date = datetime.now().date() - timedelta(days=1)
        self.assertIsNotNone(p.current_lifecycle_states)
        self.assertTrue(len(p.current_lifecycle_states) == 2)
        self.assertListEqual(
            ['End of Sale', 'End of New Service Attachment Date'],
            p.current_lifecycle_states
        )

        # set an end_of_sw_maintenance_date date
        p.end_of_sw_maintenance_date = datetime.now().date() - timedelta(days=1)
        self.assertIsNotNone(p.current_lifecycle_states)
        self.assertTrue(len(p.current_lifecycle_states) == 3)
        self.assertListEqual(
            ['End of Sale', 'End of New Service Attachment Date', 'End of SW Maintenance Releases Date'],
            p.current_lifecycle_states
        )

        # set an end_of_routine_failure_analysis date
        p.end_of_routine_failure_analysis = datetime.now().date() - timedelta(days=1)
        self.assertIsNotNone(p.current_lifecycle_states)
        self.assertTrue(len(p.current_lifecycle_states) == 4)
        self.assertListEqual(
            ['End of Sale', 'End of New Service Attachment Date',
             'End of SW Maintenance Releases Date', 'End of Routine Failure Analysis Date'],
            p.current_lifecycle_states
        )

        # set an end_of_service_contract_renewal date
        p.end_of_service_contract_renewal = datetime.now().date() - timedelta(days=1)
        self.assertIsNotNone(p.current_lifecycle_states)
        self.assertTrue(len(p.current_lifecycle_states) == 5)
        self.assertListEqual(
            ['End of Sale', 'End of New Service Attachment Date',
             'End of SW Maintenance Releases Date', 'End of Routine Failure Analysis Date',
             'End of Service Contract Renewal Date'],
            p.current_lifecycle_states
        )

        # set an end_of_service_contract_renewal date
        p.end_of_sec_vuln_supp_date = datetime.now().date() - timedelta(days=1)
        self.assertIsNotNone(p.current_lifecycle_states)
        self.assertTrue(len(p.current_lifecycle_states) == 6)
        self.assertListEqual(
            ['End of Sale', 'End of New Service Attachment Date',
             'End of SW Maintenance Releases Date', 'End of Routine Failure Analysis Date',
             'End of Service Contract Renewal Date', 'End of Vulnerability/Security Support date'],
            p.current_lifecycle_states
        )

        # set an end_of_support date
        p.end_of_support_date = datetime.now().date() - timedelta(days=1)
        self.assertIsNotNone(p.current_lifecycle_states)
        self.assertTrue(len(p.current_lifecycle_states) == 1)
        self.assertListEqual(
            ['End of Support'],
            p.current_lifecycle_states
        )
