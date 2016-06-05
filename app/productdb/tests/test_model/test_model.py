from datetime import timedelta

from django.test import TestCase
from django.utils.datetime_safe import datetime

from app.productdb.models import Vendor, Product


class VendorDataModelTest(TestCase):
    fixtures = ['default_vendors.yaml']

    def test_delete_fail_for_default_value(self):
        """
        This test should ensure, that the value "unassigned" cannot be deleted
        :return:
        """
        try:
            Vendor.objects.get(id=0).delete()
            self.fail("Exception not thrown, delete possible but it should not")

        except Exception as ex:
            self.assertEquals("Operation not allowed", str(ex))

    def test_delete_pass_for_vendor_default_value(self):
        """
        This test should ensure, that the value "unassigned" cannot be deleted
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
