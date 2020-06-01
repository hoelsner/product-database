"""
Test suite for the productdb.views module
"""
import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser, Permission, User
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.http import Http404
from django.test import RequestFactory
from app.productdb import views
from app.productdb import models

pytestmark = pytest.mark.django_db


def patch_contrib_messages(request):
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)

    return messages


@pytest.mark.usefixtures("import_default_vendors")
class TestHomeView:
    URL_NAME = "productdb:home"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.home(request)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.home(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        response = views.home(request)

        assert response.status_code == 200, "Should be callable"


@pytest.mark.usefixtures("import_default_vendors")
class TestAboutView:
    URL_NAME = "productdb:about"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.about_view(request)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.about_view(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        response = views.about_view(request)

        assert response.status_code == 200, "Should be callable"


@pytest.mark.usefixtures("import_default_vendors")
class TestBrowseVendorProductsView:
    URL_NAME = "productdb:browse_vendor_products"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.browse_vendor_products(request)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.browse_vendor_products(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        response = views.browse_vendor_products(request)

        assert response.status_code == 200, "Should be callable"

    def test_select_vendor_default(self):
        url = reverse(self.URL_NAME)
        # a predefined value should be selected by default
        default_vendor = '<option value="1" selected>Cisco Systems</option>'
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.browse_vendor_products(request)

        assert response.status_code == 200, "Should be callable"
        assert default_vendor in response.content.decode()

    def test_select_vendor_by_user(self):
        url = reverse(self.URL_NAME)
        selected_vendor = '<option value="2" selected>Juniper Networks</option>'
        data = {"vendor_selection": 2}
        request = RequestFactory().post(url, data=data)
        request.user = AnonymousUser()
        response = views.browse_vendor_products(request)

        assert response.status_code == 200, "Should be callable"
        assert selected_vendor in response.content.decode()

        # call with invalid ID
        default_vendor = '<option value="1" selected>Cisco Systems</option>'
        data = {"vendor_selection": 999}
        request = RequestFactory().post(url, data=data)
        request.user = AnonymousUser()
        response = views.browse_vendor_products(request)

        assert response.status_code == 200, "Should be callable"
        assert selected_vendor not in response.content.decode()
        assert default_vendor in response.content.decode()


@pytest.mark.usefixtures("import_default_vendors")
class TestBrowseAllProductsView:
    URL_NAME = "productdb:all_products"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.browse_all_products(request)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.browse_all_products(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        response = views.browse_all_products(request)

        assert response.status_code == 200, "Should be callable"


@pytest.mark.usefixtures("import_default_vendors")
class TestListProductGroupsView:
    URL_NAME = "productdb:list-product_groups"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.list_product_groups(request)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.list_product_groups(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        response = views.list_product_groups(request)

        assert response.status_code == 200, "Should be callable"


@pytest.mark.usefixtures("import_default_vendors")
class TestListProductListsView:
    URL_NAME = "productdb:list-product_lists"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.list_product_lists(request)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.list_product_lists(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        response = views.list_product_lists(request)

        assert response.status_code == 200, "Should be callable"


@pytest.mark.usefixtures("import_default_vendors")
class TestDetailProductGroupView:
    URL_NAME = "productdb:detail-product_group"

    def test_without_parameter(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.detail_product_group(request)

        assert response.status_code == 302, "Should redirect to list-product_groups view"
        assert response.url == reverse("productdb:list-product_groups")

    def test_url_format(self):
        # call detail URL without a parameter must result in a sub-URL which can be extended
        # to a full detail URL (required for Datatable rendering)
        pg = models.ProductGroup.objects.create(name="Product Group for testing")
        dt_url = reverse(self.URL_NAME)
        full_url = reverse(self.URL_NAME, kwargs={"product_group_id": pg.id})

        assert full_url.startswith(dt_url), "detail URL without a parameter must result in a sub-URL"

    def test_404(self):
        url = reverse(self.URL_NAME, kwargs={"product_group_id": 9999})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        with pytest.raises(Http404):
            views.detail_product_group(request, 9999)

    def test_anonymous_default(self):
        pg = models.ProductGroup.objects.create(name="Product Group for testing")
        url = reverse(self.URL_NAME, kwargs={"product_group_id": pg.id})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.detail_product_group(request, pg.id)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        pg = models.ProductGroup.objects.create(name="Product Group for testing")
        url = reverse(self.URL_NAME, kwargs={"product_group_id": pg.id})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.detail_product_group(request, pg.id)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        pg = models.ProductGroup.objects.create(name="Product Group for testing")
        url = reverse(self.URL_NAME, kwargs={"product_group_id": pg.id})
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        response = views.detail_product_group(request, pg.id)

        assert response.status_code == 200, "Should be callable"


class TestShareProductListView:
    URL_NAME = "productdb:share-product_list"

    def test_404(self):
        url = reverse(self.URL_NAME, kwargs={"product_list_id": 9999})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        with pytest.raises(Http404):
            views.share_product_list(request, 9999)

    @pytest.mark.usefixtures("import_default_vendors")
    def test_anonymous_default(self):
        u = User.objects.create(username="pdb_user")
        v = models.Vendor.objects.get(id=1)
        p = models.Product.objects.create(product_id="test product", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=p.product_id,
            vendor=v,
            update_user=u
        )
        url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.share_product_list(request, pl.id)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    @pytest.mark.usefixtures("import_default_vendors")
    def test_anonymous_login_only_mode(self):
        u = User.objects.create(username="pdb_user")
        v = models.Vendor.objects.get(id=1)
        p = models.Product.objects.create(product_id="test product", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=p.product_id,
            vendor=v,
            update_user=u
        )
        url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.share_product_list(request, pl.id)

        assert response.status_code == 200, "Share link is also callable in login only mode"

    @pytest.mark.usefixtures("import_default_vendors")
    def test_authenticated_user(self):
        u = User.objects.create(username="pdb_user")
        v = models.Vendor.objects.get(id=1)
        p = models.Product.objects.create(product_id="test product", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=p.product_id,
            vendor=v,
            update_user=u
        )
        url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})
        request = RequestFactory().get(url)
        request.user = u
        response = views.share_product_list(request, pl.id)

        assert response.status_code == 200, "Should be callable"


@pytest.mark.usefixtures("import_default_vendors")
class TestDetailProductListView:
    URL_NAME = "productdb:detail-product_list"

    def test_without_parameter(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.detail_product_list(request)

        assert response.status_code == 302, "Should redirect to list-product_list view"
        assert response.url == reverse("productdb:list-product_lists")

    def test_url_format(self):
        # call detail URL without a parameter must result in a sub-URL which can be extended
        # to a full detail URL (required for Datatable rendering)
        u = User.objects.create(username="pdb_user")
        v = models.Vendor.objects.get(id=1)
        p = models.Product.objects.create(product_id="test product", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=p.product_id,
            vendor=v,
            update_user=u
        )
        dt_url = reverse(self.URL_NAME)
        full_url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})

        assert full_url.startswith(dt_url), "detail URL without a parameter must result in a sub-URL"

    def test_404(self):
        url = reverse(self.URL_NAME, kwargs={"product_list_id": 9999})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        with pytest.raises(Http404):
            views.detail_product_list(request, 9999)

    def test_anonymous_default(self):
        u = User.objects.create(username="pdb_user")
        v = models.Vendor.objects.get(id=1)
        p = models.Product.objects.create(product_id="test product", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=p.product_id,
            vendor=v,
            update_user=u
        )
        url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.detail_product_list(request, pl.id)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        u = User.objects.create(username="pdb_user")
        v = models.Vendor.objects.get(id=1)
        p = models.Product.objects.create(product_id="test product", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=p.product_id,
            vendor=v,
            update_user=u
        )
        url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.detail_product_list(request, pl.id)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url.startswith("/productdb/share/productlist/"), \
            "if the user is not logged in, it is redirected to the sharelink"

    def test_authenticated_user(self):
        u = User.objects.create(username="pdb_user")
        v = models.Vendor.objects.get(id=1)
        p = models.Product.objects.create(product_id="test product", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=p.product_id,
            vendor=v,
            update_user=u
        )
        url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        response = views.detail_product_list(request, pl.id)

        assert response.status_code == 200, "Should be callable"


class TestProductDetailsView:
    URL_NAME = "productdb:product-detail"

    @pytest.mark.usefixtures("import_default_vendors")
    def test_without_parameter(self):
        url = reverse("productdb:product-list")
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.view_product_details(request)

        assert response.status_code == 302, "Should redirect to list-product_list view"
        assert response.url == reverse("productdb:all_products")

    @pytest.mark.usefixtures("import_default_vendors")
    def test_url_format(self):
        # call detail URL without a parameter must result in a sub-URL which can be extended
        # to a full detail URL (required for Datatable rendering)
        p = models.Product.objects.create(product_id="test product")
        dt_url = reverse("productdb:product-list")
        full_url = reverse(self.URL_NAME, kwargs={"product_id": p.id})

        assert full_url.startswith(dt_url), "detail URL without a parameter must result in a sub-URL"

    def test_404(self):
        url = reverse(self.URL_NAME, kwargs={"product_id": 9999})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        with pytest.raises(Http404):
            views.view_product_details(request, 9999)

    @pytest.mark.usefixtures("import_default_vendors")
    def test_anonymous_default(self):
        p = models.Product.objects.create(product_id="test product")
        url = reverse(self.URL_NAME, kwargs={"product_id": p.id})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.view_product_details(request, p.id)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    @pytest.mark.usefixtures("import_default_vendors")
    def test_anonymous_login_only_mode(self):
        p = models.Product.objects.create(product_id="test product")
        url = reverse(self.URL_NAME, kwargs={"product_id": p.id})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.view_product_details(request, p.id)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    @pytest.mark.usefixtures("import_default_vendors")
    def test_authenticated_user(self):
        p = models.Product.objects.create(product_id="test product")
        url = reverse(self.URL_NAME, kwargs={"product_id": p.id})
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        response = views.view_product_details(request, p.id)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("import_default_vendors")
    def test_detail_view_with_migration_options(self):
        # create basic object structure
        group1 = models.ProductMigrationSource.objects.create(name="Group One")
        group2 = models.ProductMigrationSource.objects.create(name="Group Two", preference=100)
        root_product = models.Product.objects.create(product_id="C2960XS", vendor=models.Vendor.objects.get(id=1))
        p11 = models.Product.objects.create(product_id="C2960XL", vendor=models.Vendor.objects.get(id=1))
        p12 = models.Product.objects.create(product_id="C2960XT", vendor=models.Vendor.objects.get(id=1))
        p23 = models.Product.objects.create(product_id="C2960XR", vendor=models.Vendor.objects.get(id=1))
        models.ProductMigrationOption.objects.create(
            product=root_product, migration_source=group1,
            replacement_product_id=p11.product_id
        )
        models.ProductMigrationOption.objects.create(
            product=root_product, migration_source=group2,
            replacement_product_id=p12.product_id
        )
        # p12 is replaced by 23 by group 2
        models.ProductMigrationOption.objects.create(
            product=p12, migration_source=group2,
            replacement_product_id=p23.product_id
        )

        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        for pid in [root_product.id, p11.id, p12.id, p23.id]:
            url = reverse(self.URL_NAME, kwargs={"product_id": pid})
            request = RequestFactory().get(url)
            request.user = user
            response = views.view_product_details(request, pid)

            assert response.status_code == 200, "Should be callable"


@pytest.mark.usefixtures("import_default_vendors")
class TestAddProductListView:
    URL_NAME = "productdb:add-product_list"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.add_product_list(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.add_product_list(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        url = reverse(self.URL_NAME)
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        request = RequestFactory().get(url)
        request.user = user

        # should throw a permission error
        with pytest.raises(PermissionDenied):
            views.add_product_list(request)

        # update user permissions
        perm = Permission.objects.get(codename="add_productlist")
        user = User.objects.create(username="validuser", is_superuser=False, is_staff=False)
        user.user_permissions.add(perm)
        user.save()

        request = RequestFactory().get(url)
        request.user = user
        response = views.add_product_list(request)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("import_default_vendors")
    def test_post(self):
        url = reverse(self.URL_NAME)
        perm = Permission.objects.get(codename="add_productlist")
        v = models.Vendor.objects.get(id=1)
        p = models.Product.objects.create(product_id="test product", vendor=v)
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        user.user_permissions.add(perm)
        user.save()

        data = {
            "name": "My Product List",
            "description": "My description",
            "string_product_list": p.product_id,
            "vendor": v.id
        }
        request = RequestFactory().post(url, data=data, follow=True)
        request.user = user
        response = views.add_product_list(request)

        assert response.status_code == 302
        assert response.url == reverse("productdb:list-product_lists")
        assert models.ProductList.objects.count() == 1, "One element should be created in the database"


@pytest.mark.usefixtures("import_default_vendors")
class TestEditProductListView:
    URL_NAME = "productdb:edit-product_list"

    def test_404(self):
        url = reverse(self.URL_NAME, kwargs={"product_list_id": 9999})
        request = RequestFactory().get(url)
        perm = Permission.objects.get(codename="change_productlist")
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        request.user = user
        user.user_permissions.add(perm)
        user.save()

        with pytest.raises(Http404):
            views.edit_product_list(request, 9999)

    def test_anonymous_default(self):
        u = User.objects.create(username="pdb_user")
        v = models.Vendor.objects.get(id=1)
        models.Product.objects.create(product_id="test product A", vendor=v)
        models.Product.objects.create(product_id="test product B", vendor=v)
        models.Product.objects.create(product_id="test product C", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=";".join(models.Product.objects.all().values_list("product_id", flat=True)),
            vendor=v,
            update_user=u
        )
        url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.edit_product_list(request, pl.id)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        u = User.objects.create(username="pdb_user")
        v = models.Vendor.objects.get(id=1)
        models.Product.objects.create(product_id="test product A", vendor=v)
        models.Product.objects.create(product_id="test product B", vendor=v)
        models.Product.objects.create(product_id="test product C", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=";".join(models.Product.objects.all().values_list("product_id", flat=True)),
            vendor=v,
            update_user=u
        )
        url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.edit_product_list(request, pl.id)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        v = models.Vendor.objects.get(id=1)
        models.Product.objects.create(product_id="test product A", vendor=v)
        models.Product.objects.create(product_id="test product B", vendor=v)
        models.Product.objects.create(product_id="test product C", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=";".join(models.Product.objects.all().values_list("product_id", flat=True)),
            vendor=v,
            update_user=user
        )
        url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})
        request = RequestFactory().get(url)
        request.user = user
        patch_contrib_messages(request)

        # should throw a permission error
        with pytest.raises(PermissionDenied):
            views.edit_product_list(request, pl.id)

        # update user permissions
        user = User.objects.create(username="anotheruser", is_superuser=False, is_staff=False)
        perm = Permission.objects.get(codename="change_productlist")
        user.user_permissions.add(perm)
        user.save()

        request = RequestFactory().get(url)
        request.user = user
        msgs = patch_contrib_messages(request)
        response = views.edit_product_list(request, pl.id)

        assert response.status_code == 200, "Should be callable"
        assert msgs.added_new is True
        expected_error = "You are not allowed to change this Product List. Only the original Author is allowed to " \
                         "perform this action."
        assert expected_error in response.content.decode()

    def test_post(self):
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        v = models.Vendor.objects.get(id=1)
        p = models.Product.objects.create(product_id="test product A", vendor=v)
        models.Product.objects.create(product_id="test product B", vendor=v)
        models.Product.objects.create(product_id="test product C", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=";".join(models.Product.objects.all().values_list("product_id", flat=True)),
            vendor=v,
            update_user=user
        )
        url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})
        perm = Permission.objects.get(codename="change_productlist")
        user = User.objects.create(username="anotheruser", is_superuser=False, is_staff=False)
        user.user_permissions.add(perm)
        user.save()

        # another user try to change the product list, but only the original creator is
        # allowed to change it
        data = {
            "name": "My Product List",
            "description": "My description",
            "string_product_list": p.product_id,
            "vendor": v.id
        }
        request = RequestFactory().post(url, data=data, follow=True)
        request.user = user
        patch_contrib_messages(request)
        response = views.edit_product_list(request, pl.id)

        assert response.status_code == 200
        expected_error = "You are not allowed to change this Product List. Only the original Author is allowed to " \
                         "perform this action."
        assert expected_error in response.content.decode()

        # original user try to change the product list
        data = {
            "name": "My Product List",
            "description": "My description",
            "string_product_list": p.product_id,
            "vendor": v.id
        }
        request = RequestFactory().post(url, data=data, follow=True)
        pl.update_user.user_permissions.add(perm)
        request.user = pl.update_user
        patch_contrib_messages(request)
        response = views.edit_product_list(request, pl.id)

        assert response.status_code == 302
        assert response.url == reverse("productdb:list-product_lists")
        assert models.ProductList.objects.count() == 1, "One element should be created in the database"


@pytest.mark.usefixtures("import_default_vendors")
class TestDeleteProductListView:
    URL_NAME = "productdb:delete-product_list"

    def test_404(self):
        url = reverse(self.URL_NAME, kwargs={"product_list_id": 9999})
        request = RequestFactory().get(url)
        perm = Permission.objects.get(codename="delete_productlist")
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        request.user = user
        user.user_permissions.add(perm)
        user.save()

        with pytest.raises(Http404):
            views.delete_product_list(request, 9999)

    def test_anonymous_default(self):
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        v = models.Vendor.objects.get(id=1)
        models.Product.objects.create(product_id="test product A", vendor=v)
        models.Product.objects.create(product_id="test product B", vendor=v)
        models.Product.objects.create(product_id="test product C", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=";".join(models.Product.objects.all().values_list("product_id", flat=True)),
            vendor=v,
            update_user=user
        )
        url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.delete_product_list(request, pl.id)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        v = models.Vendor.objects.get(id=1)
        models.Product.objects.create(product_id="test product A", vendor=v)
        models.Product.objects.create(product_id="test product B", vendor=v)
        models.Product.objects.create(product_id="test product C", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=";".join(models.Product.objects.all().values_list("product_id", flat=True)),
            vendor=v,
            update_user=user
        )
        url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.delete_product_list(request, pl.id)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        v = models.Vendor.objects.get(id=1)
        models.Product.objects.create(product_id="test product A", vendor=v)
        models.Product.objects.create(product_id="test product B", vendor=v)
        models.Product.objects.create(product_id="test product C", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=";".join(models.Product.objects.all().values_list("product_id", flat=True)),
            vendor=v,
            update_user=user
        )
        url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})
        user = User.objects.create(username="anotheruser", is_superuser=False, is_staff=False)
        request = RequestFactory().get(url)
        request.user = user
        patch_contrib_messages(request)

        # should throw a permission error
        with pytest.raises(PermissionDenied):
            views.delete_product_list(request, pl.id)

        # update user permissions
        perm = Permission.objects.get(codename="delete_productlist")
        user = User.objects.create(username="yetanotheruser", is_superuser=False, is_staff=False)
        user.user_permissions.add(perm)
        user.save()

        request = RequestFactory().get(url)
        request.user = user
        msgs = patch_contrib_messages(request)
        response = views.delete_product_list(request, pl.id)

        assert response.status_code == 200, "Should be callable"
        assert msgs.added_new is True, "Message should be added"
        expected_message = "You are not allowed to change this Product List. Only the " \
                           "original Author is allowed to perform this action."
        assert expected_message in response.content.decode()

        # get delete view with correct user
        perm = Permission.objects.get(codename="delete_productlist")
        pl.update_user.user_permissions.add(perm)
        pl.update_user.save()

        request = RequestFactory().get(url)
        request.user = pl.update_user
        patch_contrib_messages(request)
        response = views.delete_product_list(request, pl.id)

        assert response.status_code == 200, "Should be callable"
        assert msgs.added_new is True, "Message should be added"
        expected_message = "Be careful, this action cannot be undone!"
        assert expected_message in response.content.decode()

    def test_post(self):
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        v = models.Vendor.objects.get(id=1)
        models.Product.objects.create(product_id="test product A", vendor=v)
        models.Product.objects.create(product_id="test product B", vendor=v)
        models.Product.objects.create(product_id="test product C", vendor=v)
        pl = models.ProductList.objects.create(
            name="PG",
            string_product_list=";".join(models.Product.objects.all().values_list("product_id", flat=True)),
            vendor=v,
            update_user=user
        )
        url = reverse(self.URL_NAME, kwargs={"product_list_id": pl.id})
        perm = Permission.objects.get(codename="delete_productlist")
        user = User.objects.create(username="anotheruser", is_superuser=False, is_staff=False)
        user.user_permissions.add(perm)
        user.save()

        # another user try to change the product list, but only the original creator is
        # allowed to change it
        data = {
            "really_delete": True
        }
        request = RequestFactory().post(url, data=data, follow=True)
        request.user = user
        msgs = patch_contrib_messages(request)
        response = views.delete_product_list(request, pl.id)

        assert response.status_code == 200
        assert msgs.added_new is True
        expected_error = "You are not allowed to change this Product List. Only the original Author is allowed to " \
                         "perform this action."
        assert expected_error in response.content.decode()

        # original user try to change the product list
        data = {
            "really_delete": True
        }
        request = RequestFactory().post(url, data=data, follow=True)
        pl.update_user.user_permissions.add(perm)
        request.user = pl.update_user
        msgs = patch_contrib_messages(request)
        response = views.delete_product_list(request, pl.id)

        assert response.status_code == 302
        assert response.url == reverse("productdb:list-product_lists")
        assert msgs.added_new is True
        assert models.ProductList.objects.count() == 0, "One element should be created in the database"


@pytest.mark.usefixtures("import_default_vendors")
class TestImportProductMigrationsView:
    URL_NAME = "productdb:import_product_migrations"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.import_product_migrations(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.import_product_migrations(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        # the import product dialog requires the change_product permission
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)

        with pytest.raises(PermissionDenied):
            views.import_product_migrations(request)

        request = RequestFactory().get(url)
        user = User.objects.create(username="anotheruser", is_superuser=False, is_staff=False)
        user.user_permissions.add(Permission.objects.get(codename="change_productmigrationoption"))
        request.user = user
        response = views.import_product_migrations(request)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("disable_import_product_migrations_task")
    def test_post(self):
        url = reverse(self.URL_NAME)
        user = User.objects.create(username="test", is_superuser=False, is_staff=False)
        user.user_permissions.add(Permission.objects.get(codename="change_productmigrationoption"))
        user.save()

        # content is not relevant for this test
        request = RequestFactory().post(url, data={"excel_file": SimpleUploadedFile("myfile.xlsx", b"yxz")})
        request.user = user

        response = views.import_product_migrations(request)

        assert response.status_code == 302, "redirect to task in progress view"
        assert response.url == reverse("task_in_progress", kwargs={"task_id": "mock_task_id"})

    @pytest.mark.usefixtures("disable_import_product_migrations_task")
    def test_post_as_superuser(self):
        url = reverse(self.URL_NAME)
        user = User.objects.create(username="testuser", is_superuser=True, is_staff=False)
        user.user_permissions.add(Permission.objects.get(codename="change_productmigrationoption"))
        user.save()

        # content is not relevant for this test
        request = RequestFactory().post(url, data={"excel_file": SimpleUploadedFile("myfile.xlsx", b"yxz")})
        request.user = user

        response = views.import_product_migrations(request)

        assert response.status_code == 302, "redirect to task in progress view"
        assert response.url == reverse("task_in_progress", kwargs={"task_id": "mock_task_id"})


@pytest.mark.usefixtures("import_default_vendors")
class TestImportProductsView:
    URL_NAME = "productdb:import_products"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.import_products(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.import_products(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        # the import product dialog requires the change_product permission
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = user

        with pytest.raises(PermissionDenied):
            views.import_products(request)

        request = RequestFactory().get(url)
        user = User.objects.create(username="anotheruser", is_superuser=False, is_staff=False)
        user.user_permissions.add(Permission.objects.get(codename="change_product"))
        request.user = user
        response = views.import_products(request)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("disable_import_price_list_task")
    def test_post(self):
        url = reverse(self.URL_NAME)
        user = User.objects.create(username="test", is_superuser=False, is_staff=False)
        user.user_permissions.add(Permission.objects.get(codename="change_product"))
        user.save()

        # content is not relevant for this test
        request = RequestFactory().post(url, data={
            "excel_file": SimpleUploadedFile("myfile.xlsx", b"yxz")
        })
        request.user = user

        response = views.import_products(request)

        assert response.status_code == 302, "redirect to task in progress view"
        assert response.url == reverse("task_in_progress", kwargs={"task_id": "mock_task_id"})

    @pytest.mark.usefixtures("disable_import_price_list_task")
    def test_post_as_superuser(self):
        url = reverse(self.URL_NAME)
        user = User.objects.create(username="test", is_superuser=True, is_staff=False)
        user.user_permissions.add(Permission.objects.get(codename="change_product"))
        user.save()

        # content is not relevant for this test
        request = RequestFactory().post(url, data={
            "excel_file": SimpleUploadedFile("myfile.xlsx", b"yxz")
        })
        request.user = user

        response = views.import_products(request)

        assert response.status_code == 302, "redirect to task in progress view"
        assert response.url == reverse("task_in_progress", kwargs={"task_id": "mock_task_id"})


@pytest.mark.usefixtures("import_default_vendors")
class TestEditUserProfileView:
    URL_NAME = "productdb:edit-user_profile"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.edit_user_profile(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.edit_user_profile(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        # the import product dialog requires the change_product permission
        url = reverse(self.URL_NAME)
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)

        request = RequestFactory().get(url)
        request.user = user
        response = views.edit_user_profile(request)

        assert response.status_code == 200, "Should be callable"

    def test_user_email_is_set_as_initial_value(self):
        pass

    @pytest.mark.usefixtures("disable_import_price_list_task")
    def test_post(self):
        url = reverse(self.URL_NAME)
        user = User.objects.create(username="test", is_superuser=False, is_staff=False)

        request = RequestFactory().post(url, data={
            "email": "a@b.com",
            "preferred_vendor": 1
        })
        request.user = user
        msgs = patch_contrib_messages(request)

        response = views.edit_user_profile(request)

        assert response.status_code == 302, "redirect to task in progress view"
        assert msgs.added_new is True
        assert response.url == reverse("productdb:home")

    @pytest.mark.usefixtures("disable_import_price_list_task")
    def test_post_with_back_to_link(self):
        url = reverse(self.URL_NAME) + "?back_to=" + reverse("productdb:about")
        user = User.objects.create(username="test", is_superuser=False, is_staff=False)

        request = RequestFactory().post(url, data={
            "email": "a@b.com",
            "preferred_vendor": 1
        })
        request.user = user
        msgs = patch_contrib_messages(request)

        response = views.edit_user_profile(request)

        assert response.status_code == 302, "redirect to task in progress view"
        assert msgs.added_new is True
        assert response.url == reverse("productdb:about"), "Should return to the back_to reference"


@pytest.mark.usefixtures("import_default_vendors")
class TestListProductCheckView:
    URL_NAME = "productdb:list-product_checks"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.list_product_checks(request)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    @pytest.mark.usefixtures("import_default_vendors")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.list_product_checks(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    @pytest.mark.usefixtures("import_default_vendors")
    def test_authenticated_user(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        response = views.list_product_checks(request)

        assert response.status_code == 200, "Should be callable"


@pytest.mark.usefixtures("import_default_vendors")
class TestDetailProductCheckView:
    URL_NAME = "productdb:detail-product_check"

    def test_anonymous_default(self):
        pc = models.ProductCheck.objects.create(name="Test", input_product_ids="Test")
        parameters = {"product_check_id": pc.id}
        url = reverse(self.URL_NAME, kwargs=parameters)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.detail_product_check(request, **parameters)

        assert response.status_code == 200, "Should be callable"

    @pytest.mark.usefixtures("enable_login_only_mode")
    @pytest.mark.usefixtures("import_default_vendors")
    def test_anonymous_login_only_mode(self):
        pc = models.ProductCheck.objects.create(name="Test", input_product_ids="Test")
        parameters = {"product_check_id": pc.id}
        url = reverse(self.URL_NAME, kwargs=parameters)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.detail_product_check(request, **parameters)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    @pytest.mark.usefixtures("import_default_vendors")
    def test_authenticated_user(self):
        pc = models.ProductCheck.objects.create(name="Test", input_product_ids="Test")
        parameters = {"product_check_id": pc.id}
        url = reverse(self.URL_NAME, kwargs=parameters)
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        response = views.detail_product_check(request, **parameters)

        assert response.status_code == 200, "Should be callable"

    def test_404(self):
        parameters = {"product_check_id": 9999}
        url = reverse(self.URL_NAME, kwargs=parameters)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        with pytest.raises(Http404):
            views.detail_product_check(request, **parameters)

    @pytest.mark.usefixtures("import_default_vendors")
    def test_in_progress_redirect(self):
        pc = models.ProductCheck.objects.create(name="Test", input_product_ids="Test")
        pc.task_id = "1234"  # if task ID is set, a redirect to the task in progress should occur
        pc.save()
        assert pc.in_progress is True

        parameters = {"product_check_id": pc.id}
        url = reverse(self.URL_NAME, kwargs=parameters)
        request = RequestFactory().get(url)
        request.user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        response = views.detail_product_check(request, **parameters)

        assert response.status_code == 302
        assert response.url.startswith("/productdb/task/")


@pytest.mark.usefixtures("import_default_vendors")
@pytest.mark.usefixtures("set_celery_always_eager")
class TestCreateProductCheckView:
    URL_NAME = "productdb:create-product_check"

    def test_anonymous_default(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.create_product_check(request)

        assert response.status_code == 200, "Should be callable without login"

    @pytest.mark.usefixtures("enable_login_only_mode")
    def test_anonymous_login_only_mode(self):
        url = reverse(self.URL_NAME)
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        response = views.create_product_check(request)

        assert response.status_code == 302, "Should redirect to login page"
        assert response.url == reverse("login") + "?next=" + url, \
            "Should contain a next parameter for redirect"

    def test_authenticated_user(self):
        url = reverse(self.URL_NAME)
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)

        request = RequestFactory().get(url)
        request.user = user
        response = views.create_product_check(request)

        assert response.status_code == 200, "Should be callable without permissions"

    @pytest.mark.usefixtures("import_default_vendors")
    def test_post(self):
        url = reverse(self.URL_NAME)
        perm = Permission.objects.get(codename="add_productcheck")
        p = models.Product.objects.create(product_id="test product")
        user = User.objects.create(username="testuser", is_superuser=False, is_staff=False)
        user.user_permissions.add(perm)
        user.save()

        data = {
            "name": "My Product check",
            "input_product_ids": "test"
        }
        request = RequestFactory().post(url, data=data, follow=True)
        request.user = user
        response = views.create_product_check(request)

        assert response.status_code == 302
        assert response.url.startswith("/productdb/task/")
        assert models.ProductCheck.objects.count() == 1, "One element should be created in the database"

        # test public product check
        data = {
            "name": "My Product check",
            "input_product_ids": "test",
            "public_product_check": "on"
        }
        request = RequestFactory().post(url, data=data, follow=True)
        request.user = user
        response = views.create_product_check(request)

        assert response.status_code == 302
        assert response.url.startswith("/productdb/task/")
        assert models.ProductCheck.objects.count() == 2, "One element should be created in the database"
