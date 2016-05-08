from django.test import TestCase
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

        except Exception as ex:
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
