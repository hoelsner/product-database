from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from app.productdb.models import ProductList, Product, Vendor


class ProductListViewTest(TestCase):
    fixtures = ["default_users.yaml", "default_vendors.yaml"]

    def test_share_product_list_link(self):
        Product.objects.create(product_id="Test", vendor=Vendor.objects.get(id=1))
        pl = ProductList.objects.create(
            name="Name", description="Description", string_product_list="Test", update_user=User.objects.get(username="api")
        )
        url = reverse("productdb:share-product_list", kwargs={"product_list_id": pl.id})

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200, response.content)

    def test_add_permissions(self):
        url = reverse("productdb:add-product_list")

        # add is not permitted without login (redirect to login page)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn("Please enter your credentials below.", response.content.decode("utf-8"))

        # add is not permitted without sufficient permissions
        self.client.login(username="api", password="api")

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403, response.content)

        # add is permitted with sufficient permissions
        self.client.login(username="pdb_admin", password="pdb_admin")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_edit_permission(self):
        Product.objects.create(product_id="Test", vendor=Vendor.objects.get(id=1))
        pl = ProductList.objects.create(
            name="Name", description="Description",
            string_product_list="Test", update_user=User.objects.get(username="api")
        )
        url = reverse("productdb:edit-product_list", kwargs={"product_list_id": pl.id})

        # edit is not permitted without login (redirect to login page)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn("Please enter your credentials below.", response.content.decode("utf-8"))

        # edit is not permitted without sufficient permissions
        self.client.login(username="api", password="api")

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403, response.content)

        # edit is not permitted if the edit user is not the same as the creating user
        self.client.login(username="pdb_admin", password="pdb_admin")

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200, response.content.decode("utf-8"))
        msg = "You are not allowed to change this Product List. Only the original Author is allowed to perform this " \
              "action."
        self.assertIn(msg, response.content.decode("utf-8"))

        # edit is permitted with sufficient permissions
        pl.update_user = User.objects.get(username="pdb_admin")
        pl.save()
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200, response.content.decode("utf-8"))
        msg = "You are not allowed to change this Product List. Only the original Author is allowed to perform this " \
              "action."
        self.assertNotIn(msg, response.content.decode("utf-8"))

    def test_delete_permission(self):
        Product.objects.create(product_id="Test", vendor=Vendor.objects.get(id=1))
        pl = ProductList.objects.create(
            name="Name", description="Description",
            string_product_list="Test", update_user=User.objects.get(username="api")
        )
        url = reverse("productdb:delete-product_list", kwargs={"product_list_id": pl.id})

        # edit is not permitted without login (redirect to login page)
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn("Please enter your credentials below.", response.content.decode("utf-8"))

        # edit is not permitted without sufficient permissions
        self.client.login(username="api", password="api")

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403, response.content)

        # edit is not permitted if the edit user is not the same as the creating user
        self.client.login(username="pdb_admin", password="pdb_admin")

        response = self.client.post(url, data={"really_delete": True})
        self.assertEqual(response.status_code, 200, response.content.decode("utf-8"))
        msg = "You are not allowed to change this Product List. Only the original Author is allowed to perform this " \
              "action."
        self.assertIn(msg, response.content.decode("utf-8"))

        # edit is permitted with sufficient permissions
        pl.update_user = User.objects.get(username="pdb_admin")
        pl.save()
        response = self.client.post(url, data={"really_delete": "1"}, follow=True)
        self.assertEqual(response.status_code, 200, response.content.decode("utf-8"))
        msg = "Product List <strong>%s</strong> successfully deleted." % pl.name
        self.assertIn(msg, response.content.decode("utf-8"))
        self.assertEqual(0, ProductList.objects.all().count())


class UserProfileViewTest(TestCase):
    fixtures = ["default_users.yaml", "default_vendors.yaml"]

    def test_user_profile_edit_with_unauthenticated_user(self):
        response = self.client.get(reverse("productdb:edit-user_profile"), follow=True)
        self.assertEqual(response.status_code, 200, "should redirect to login page")
        self.assertIn("Please enter your credentials below.", response.content.decode("utf-8"))
        self.assertEqual(('/productdb/login/?next=/productdb/profile/edit/', 302), response.redirect_chain[0])

    def test_user_profile_edit_with_authenticated_user(self):
        self.client.login(username="api", password="api")
        response = self.client.get(reverse("productdb:edit-user_profile"))
        self.assertEqual(response.status_code, 200, "should view the edit page")
        self.assertIn("Edit User Profile", response.content.decode("utf-8"))
