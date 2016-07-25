from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.encoding import escape_uri_path

from app.productdb.models import ProductList, Product, Vendor, ProductGroup


def test_backlink_on_page(url, default_back_to_url, test_obj):
    # verify custom back to link
    home_url = "this_is_a_custom_backlink_that_must be part of the page"
    response = test_obj.client.get(url + "?back_to=" + escape_uri_path(home_url))

    test_obj.assertEqual(response.status_code, 200)
    test_obj.assertIn(
        "href=\"%s\"" % home_url,
        response.content.decode("utf-8"),
        "page should contain the specified link"
    )

    # verify default back to link
    response = test_obj.client.get(url)

    test_obj.assertEqual(response.status_code, 200)
    test_obj.assertIn(
        "href=\"%s\"" % default_back_to_url,
        response.content.decode("utf-8"),
        "page should contain the specified link"
    )


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

    def test_back_to_links_in_product_list_objects(self):
        Product.objects.create(product_id="Product ID")
        pl = ProductList.objects.create(
            name="Product List",
            description="",
            string_product_list="Product ID",
            update_user=User.objects.get(username="api")
        )

        # possible without authentication
        test_backlink_on_page(
            url=reverse("productdb:detail-product_list", kwargs={"product_list_id": pl.id}),
            default_back_to_url=reverse("productdb:list-product_lists"),
            test_obj=self
        )

        # permissions required
        self.client.login(username="pdb_admin", password="pdb_admin")

        test_backlink_on_page(
            url=reverse("productdb:add-product_list"),
            default_back_to_url=reverse("productdb:list-product_lists"),
            test_obj=self
        )

        test_backlink_on_page(
            url=reverse("productdb:edit-product_list", kwargs={"product_list_id": pl.id}),
            default_back_to_url=reverse("productdb:list-product_lists"),
            test_obj=self
        )

        test_backlink_on_page(
            url=reverse("productdb:delete-product_list", kwargs={"product_list_id": pl.id}),
            default_back_to_url=reverse("productdb:list-product_lists"),
            test_obj=self
        )


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


class ProductViewTest(TestCase):
    fixtures = ["default_users.yaml", "default_vendors.yaml"]

    def test_back_to_link_in_product_group_detail_view(self):
        p = Product.objects.create(product_id="Test")

        test_backlink_on_page(
            url=reverse("productdb:product-detail", kwargs={"product_id": p.id}),
            default_back_to_url=reverse("productdb:all_products"),
            test_obj=self
        )


class ProductGroupViewTest(TestCase):
    fixtures = ["default_users.yaml", "default_vendors.yaml"]

    def test_back_to_link_in_product_group_detail_view(self):
        pg = ProductGroup.objects.create(name="Test")

        test_backlink_on_page(
            url=reverse("productdb:detail-product_group", kwargs={"product_group_id": pg.id}),
            default_back_to_url=reverse("productdb:list-product_groups"),
            test_obj=self
        )
