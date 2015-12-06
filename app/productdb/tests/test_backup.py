import os
import shutil

from django.core.exceptions import ObjectDoesNotExist

from app.productdb.models import Product, ProductList
from app.productdb.tests import BaseApiUnitTest
from app.productdb.model_backup import create_backup, restore_backup


class TestBackupRestore(BaseApiUnitTest):
    """
    test and verify the backup and restore functionality
    """
    fixtures = ['default_vendors.yaml', 'default_users.yaml']
    TEST_BACKUP_DIRECTORY = os.path.join("..", "backup", "test")

    def test_backup_restore(self):
        # clean directory
        if os.path.exists(self.TEST_BACKUP_DIRECTORY):
            shutil.rmtree(self.TEST_BACKUP_DIRECTORY)

        # create test data
        product_a_name = "product A"
        product_b_name = "product B"
        productlist_a_name = "product list A"

        p1 = Product.objects.create(product_id=product_a_name)
        p2 = Product.objects.create(product_id=product_b_name)
        l = ProductList.objects.create(product_list_name=productlist_a_name)
        p1.lists.add(l)
        p1.save()
        p2.lists.add(l)
        p2.save()

        # take backup
        create_backup(self.TEST_BACKUP_DIRECTORY)

        # verify that directory and backup files exist
        self.assertTrue(os.path.exists(self.TEST_BACKUP_DIRECTORY))
        self.assertTrue(os.path.exists(os.path.join(self.TEST_BACKUP_DIRECTORY, "products.json")))
        self.assertTrue(os.path.exists(os.path.join(self.TEST_BACKUP_DIRECTORY, "product_lists.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.TEST_BACKUP_DIRECTORY, "products.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.TEST_BACKUP_DIRECTORY, "product_lists.json")))

        # clean database entries
        query = Product.objects.all()
        for e in query:
            e.delete()

        query = ProductList.objects.all()
        for e in query:
            e.delete()

        # verify that product does not exist
        with self.assertRaises(ObjectDoesNotExist):
            Product.objects.get(product_id=product_a_name)

        # restore backup
        restore_backup(self.TEST_BACKUP_DIRECTORY)

        # verify elements in the database
        receive_p1 = Product.objects.get(product_id=product_a_name)
        receive_p2 = Product.objects.get(product_id=product_b_name)
        receive_l = ProductList.objects.get(product_list_name=productlist_a_name)

        if receive_p1 not in receive_l.products.all():
            self.fail("element not in restored data")

        if receive_p2 not in receive_l.products.all():
            self.fail("element not in restored data")
