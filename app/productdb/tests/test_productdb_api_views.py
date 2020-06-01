"""
Test suite for the productdb.api_views module
"""
import base64
import pytest
from urllib.parse import quote
import pytz

import requests
from django.utils.dateformat import DateFormat
from django.utils.formats import get_format
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from django.utils.datetime_safe import date, datetime
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from app.productdb import models

from app.config.models import NotificationMessage
from app.productdb.models import Vendor, ProductGroup, Product, ProductList, ProductMigrationOption, \
    ProductMigrationSource, ProductIdNormalizationRule

pytestmark = pytest.mark.django_db


AUTH_USER = {
    "username": "api",
    "password": "api"
}
SUPER_USER = {
    "username": "pdb_admin",
    "password": "pdb_admin"
}
REST_TOKEN_AUTH = reverse("productdb:api-token-auth")
REST_TOKEN_LOGOUT = reverse("productdb:api-token-logout")
REST_VENDOR_LIST = reverse("productdb:vendors-list")
REST_VENDOR_DETAIL = REST_VENDOR_LIST + "%d/"
REST_PRODUCT_GROUP_LIST = reverse("productdb:productgroups-list")
REST_PRODUCT_GROUP_COUNT = REST_PRODUCT_GROUP_LIST + "count/"
REST_PRODUCT_GROUP_DETAIL = REST_PRODUCT_GROUP_LIST + "%d/"
REST_PRODUCT_LIST = reverse("productdb:products-list")
REST_PRODUCT_COUNT = REST_PRODUCT_LIST + "count/"
REST_PRODUCT_DETAIL = REST_PRODUCT_LIST + "%d/"
REST_PRODUCTLIST_LIST = reverse("productdb:productlists-list")
REST_PRODUCTLIST_DETAIL = REST_PRODUCTLIST_LIST + "%d/"
REST_PRODUCTMIGRATIONSOURCE_LIST = reverse("productdb:productmigrationsources-list")
REST_PRODUCTMIGRATIONSOURCE_DETAIL = REST_PRODUCTMIGRATIONSOURCE_LIST + "%d/"
REST_PRODUCTMIGRATIONOPTION_LIST = reverse("productdb:productmigrationoptions-list")
REST_PRODUCTMIGRATIONOPTION_DETAIL = REST_PRODUCTMIGRATIONOPTION_LIST + "%d/"
REST_NOTIFICATIONMESSAGES_LIST = reverse("productdb:notificationmessages-list")
REST_NOTIFICATIONMESSAGES_DETAIL = REST_NOTIFICATIONMESSAGES_LIST + "%d/"
REST_PRODUCTNORMALIZATIONRULE_LIST = reverse("productdb:productidnormalizationrules-list")
REST_PRODUCTNORMALIZATIONRULE_DETAIL = REST_PRODUCTNORMALIZATIONRULE_LIST + "%d/"

COMMON_API_ENDPOINT_BEHAVIOR = [
    REST_VENDOR_LIST,
    REST_VENDOR_DETAIL % 1,
    REST_PRODUCT_GROUP_LIST,
    REST_PRODUCT_GROUP_DETAIL % 1,
    REST_PRODUCTLIST_LIST,
    REST_PRODUCTLIST_DETAIL % 1,
    REST_PRODUCTMIGRATIONSOURCE_LIST,
    REST_PRODUCTMIGRATIONSOURCE_DETAIL % 1,
    REST_PRODUCTMIGRATIONOPTION_LIST,
    REST_PRODUCTMIGRATIONOPTION_DETAIL % 1,
    REST_NOTIFICATIONMESSAGES_LIST
]


@pytest.fixture
def common_api_endpoint_objects():
    """DB objects for the common API endpoint tests"""
    pg = models.ProductGroup.objects.create(name="Test")
    ms = models.ProductMigrationSource.objects.create(name="Test")
    models.ProductMigrationOption.objects.create(
        migration_source=ms,
        product=models.Product.objects.create(product_id="A")
    )


@pytest.mark.usefixtures("common_api_endpoint_objects")
@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
class TestCommonAPIEndpoint:
    """Test Django REST Framework API behavior"""
    def test_unauthorized_access(self):
        client = APIClient()
        for url in COMMON_API_ENDPOINT_BEHAVIOR:
            response = client.get(url)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED, "Unauthorized access not allowed by default"
            assert response["Content-Type"] == "application/json", "Should use JSON by default"
            assert response.json() == {"detail": "Authentication credentials were not provided."}

    def test_invalid_authentication(self):
        client = APIClient()
        client.login(username="api", password="invalid password")
        for url in COMMON_API_ENDPOINT_BEHAVIOR:
            response = client.get(url)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert response.json() == {'detail': 'Authentication credentials were not provided.'}

    def test_invalid_permissions(self):
        client = APIClient()
        client.login(**AUTH_USER)
        for url in COMMON_API_ENDPOINT_BEHAVIOR:
            response = client.post(url)

            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.json() == {'detail': 'You do not have permission to perform this action.'}

    def test_xml_renderer(self):
        """smoke test to verify, that the XML renderer works. Only an XML renderer is implemented therefore write
        operations using XML are not possible"""
        for e in range(1, 50):
            p = models.Product.objects.create(product_id="Foo %s" % e)

        test_queries = [
            REST_VENDOR_LIST,
            REST_PRODUCT_GROUP_LIST,
            REST_PRODUCTLIST_LIST,
            REST_PRODUCTMIGRATIONSOURCE_LIST,
            REST_PRODUCTMIGRATIONOPTION_LIST,
        ]

        client = APIClient()
        client.login(**AUTH_USER)

        for url in test_queries:
            response = client.get(url + "?format=xml")

            assert response.status_code == status.HTTP_200_OK

    def test_page_size(self):
        for e in range(1, 50):
            models.Product.objects.create(product_id="Foo %s" % e)

        client = APIClient()
        client.login(**AUTH_USER)

        # default page size is 25
        response = client.get(REST_PRODUCT_LIST)
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert jdata["pagination"]["page_records"] == 25, "default page size is 25"
        assert jdata["pagination"]["total_records"] == 50, "total records should be all products"

        # test custom page size
        response = client.get(REST_PRODUCT_LIST + "?page_size=40")
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert jdata["pagination"]["page_records"] == 40, "should contain 40 elements"
        assert jdata["pagination"]["total_records"] == 50, "total records should be all products"

        # test upper page limit
        response = client.get(REST_PRODUCT_LIST + "?page_size=1000")
        assert response.status_code == status.HTTP_200_OK

        response = client.get(REST_PRODUCT_LIST + "?page_size=1001")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_http_basic_authentication(self):
        for e in range(1, 50):
            models.Product.objects.create(product_id="Foo %s" % e)

        client = APIClient()
        response = client.post(REST_PRODUCT_LIST)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # add HTTP basic authentication to request
        credentials = base64.b64encode(f'{AUTH_USER["username"]}:{AUTH_USER["password"]}'.encode('utf-8'))
        client.credentials(HTTP_AUTHORIZATION='Basic {}'.format(credentials.decode('utf-8')))

        # test base authentication
        response = client.get(REST_PRODUCT_LIST)
        assert response.status_code == status.HTTP_200_OK

    def test_token_authentication(self):
        for e in range(1, 50):
            models.Product.objects.create(product_id="Foo %s" % e)

        client = APIClient()

        # get a token by posting the username and password to the API endpoint
        response = client.post(REST_TOKEN_AUTH, data=dict(**AUTH_USER))
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "token" in data.keys()
        previous_token = data["token"]
        client.credentials(HTTP_AUTHORIZATION="Token %s" % previous_token)

        # test that token is still working
        response = client.get(REST_PRODUCT_LIST)
        assert response.status_code == status.HTTP_200_OK

        # explicitly logout from API
        response = client.post(REST_TOKEN_LOGOUT)
        assert response.status_code == status.HTTP_200_OK

        # test that token isn't working
        response = client.get(REST_PRODUCT_LIST)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # fetch a new (and hopefully different token)
        client.login(**AUTH_USER)

        response = client.post(REST_TOKEN_AUTH, data=dict(**AUTH_USER))
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["token"] != previous_token


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
class TestVendorAPIEndpoint:
    """
    Django REST Framework API endpoint tests for the Vendor model
    """
    def test_token_authentication(self, live_server):
        token, _ = Token.objects.get_or_create(user=User.objects.get(username=AUTH_USER["username"]))

        response = requests.get(live_server + REST_VENDOR_LIST, headers={
            "Authorization": "Token %s" % token.key
        })

        assert response.status_code == status.HTTP_200_OK, response.text

        response = requests.get(live_server + REST_VENDOR_LIST, headers={
            "Authorization": "Token invalid_token"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_read_access_with_authenticated_user(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 3,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 3
            },
            "data": [
                {
                    "name": "unassigned",
                    "id": 0,
                    "url": "http://testserver/productdb/api/v1/vendors/0/"
                },
                {
                    "name": "Cisco Systems",
                    "id": 1,
                    "url": "http://testserver/productdb/api/v1/vendors/1/"
                },
                {
                    "name": "Juniper Networks",
                    "id": 2,
                    "url": "http://testserver/productdb/api/v1/vendors/2/"
                }
            ]
        }

        client = APIClient()
        client.login(**AUTH_USER)
        response = client.get(REST_VENDOR_LIST)

        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not found in result"
        assert jdata == expected_result, "unexpected result from API endpoint"

        # access first element of the list
        response = client.get(jdata["data"][0]["url"])

        assert response.status_code == status.HTTP_200_OK
        assert jdata["data"][0] == response.json()

    def test_add_access_with_permission(self):
        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="add_vendor")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.add_vendor")

        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.post(REST_VENDOR_LIST, data={"name": "Awesome Vendor"})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, "API endpoint is always read only"
        assert response.json() == {'detail': 'Method "POST" not allowed.'}
        assert Vendor.objects.count() == 3, "no additional vendor is created"

    def test_change_access_with_permission(self):
        # create a user with permissions
        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="change_vendor")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.change_vendor")

        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.put(REST_VENDOR_DETAIL % 1, data={"name": "renamed vendor"})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, "API endpoint is always read only"
        assert response.json() == {'detail': 'Method "PUT" not allowed.'}

    def test_delete_access_with_permission(self):
        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="delete_vendor")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.delete_vendor")

        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.delete(REST_VENDOR_DETAIL % 1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, "API endpoint is always read only"
        assert response.json() == {'detail': 'Method "DELETE" not allowed.'}
        assert Vendor.objects.count() == 3, "no vendor was deleted"

    def test_delete_unassigned_vendor_as_superuser(self):
        # not possible due to limitations in the model implementation
        client = APIClient()
        client.login(**SUPER_USER)
        response = client.delete(REST_VENDOR_DETAIL % 0)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, "API endpoint is always read only"
        assert response.json() == {'detail': 'Method "DELETE" not allowed.'}
        assert Vendor.objects.count() == 3, "no vendor was deleted"

    def test_search_field(self):
        """
        search field implementation contains a regular expression search on the vendor name field
        :return:
        """
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "name": "Cisco Systems",
                    "id": 1,
                    "url": "http://testserver/productdb/api/v1/vendors/1/"
                }
            ]
        }
        models.Vendor.objects.create(name="CCCCCCCi")

        client = APIClient()
        client.login(**AUTH_USER)
        # verify the use of regular expressions
        response = client.get(REST_VENDOR_LIST + "?search=" + quote("^Ci"))

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata == expected_result, "unexpected result from API endpoint"

    def test_filter_fields(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "name": "Cisco Systems",
                    "id": 1,
                    "url": "http://testserver/productdb/api/v1/vendors/1/"
                }
            ]
        }

        client = APIClient()
        client.login(**AUTH_USER)

        # use ID field filter (exact match)
        response = client.get(REST_VENDOR_LIST + "?id=1")

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata == expected_result, "unexpected result from API endpoint"

        # use name field
        response = client.get(REST_VENDOR_LIST + "?name=" + quote("Cisco Systems"))

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata == expected_result, "unexpected result from API endpoint"

        # call with empty result
        response = client.get(REST_VENDOR_LIST + "?name=" + quote("Cisco"))

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 0, "should return nothing, because an exact match is required"


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
class TestProductMigrationOptionAPIEndpoint:
    """
    Django REST Framework API endpoint tests for the ProductMigrationOption model
    """
    def test_token_authentication(self, live_server):
        token, _ = Token.objects.get_or_create(user=User.objects.get(username=AUTH_USER["username"]))

        response = requests.get(live_server + REST_PRODUCTMIGRATIONOPTION_LIST, headers={
            "Authorization": "Token %s" % token.key
        })

        assert response.status_code == status.HTTP_200_OK, response.text

        response = requests.get(live_server + REST_PRODUCTMIGRATIONOPTION_LIST, headers={
            "Authorization": "Token invalid_token"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_read_access_with_authenticated_user(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 2,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 2
            },
            "data": [
                {
                    "migration_source": 1,
                    "migration_product_info_url": None,
                    "url": "http://testserver/productdb/api/v1/productmigrationoptions/%d/",
                    "replacement_product_id": "replacement",
                    "id": 1,
                    "product": 1,
                    "comment": "",
                },
                {
                    "migration_source": 1,
                    "migration_product_info_url": None,
                    "url": "http://testserver/productdb/api/v1/productmigrationoptions/%d/",
                    "replacement_product_id": "replacement2",
                    "id": 2,
                    "product": 2,
                    "comment": "",
                }
            ]
        }
        p1 = models.Product.objects.create(vendor=Vendor.objects.get(id=1), id=1, product_id="B")
        p2 = models.Product.objects.create(vendor=Vendor.objects.get(id=1), id=2, product_id="A")
        pmg = models.ProductMigrationSource.objects.create(name="Cisco", id=1)

        pmo1 = models.ProductMigrationOption.objects.create(
            product=p1, migration_source=pmg,
            replacement_product_id=expected_result["data"][0]["replacement_product_id"], comment=""
        )
        pmo2 = models.ProductMigrationOption.objects.create(
            product=p2, migration_source=pmg,
            replacement_product_id=expected_result["data"][1]["replacement_product_id"], comment=""
        )
        expected_result["data"][0]["id"] = pmo1.id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % pmo1.id
        expected_result["data"][0]["comment"] = pmo1.comment
        expected_result["data"][1]["id"] = pmo2.id
        expected_result["data"][1]["url"] = expected_result["data"][1]["url"] % pmo2.id
        expected_result["data"][1]["comment"] = pmo2.comment

        client = APIClient()
        client.login(**AUTH_USER)
        response = client.get(REST_PRODUCTMIGRATIONOPTION_LIST)

        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not found in result"
        assert jdata == expected_result, "unexpected result from API endpoint"

        # access first element of the list
        response = client.get(jdata["data"][0]["url"])

        assert response.status_code == status.HTTP_200_OK
        assert jdata["data"][0] == response.json()

    def test_add_access_with_permission(self):
        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="add_productmigrationoption")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.add_productmigrationoption")

        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.post(REST_PRODUCTMIGRATIONOPTION_LIST,
                               data={"replacement_id": "Awesome Product Migration Option"})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, "API endpoint is always read only"
        assert response.json() == {'detail': 'Method "POST" not allowed.'}
        assert ProductMigrationOption.objects.count() == 0, "no additional product migration option is created"

    def test_change_access_with_permission(self):
        # create a user with permissions
        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="change_productmigrationoption")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.change_productmigrationoption")

        models.ProductMigrationOption.objects.create(
            product=models.Product.objects.create(product_id="test pid"),
            migration_source=models.ProductMigrationSource.objects.create(name="test")
        )
        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.put(REST_PRODUCTMIGRATIONOPTION_DETAIL % 1, data={
            "comment": "renamed product migration source"
        })

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, "API endpoint is always read only"
        assert response.json() == {'detail': 'Method "PUT" not allowed.'}

    def test_delete_access_with_permission(self):
        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="delete_productmigrationoption")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.delete_productmigrationoption")

        models.ProductMigrationOption.objects.create(
            product=models.Product.objects.create(product_id="test pid"),
            migration_source=models.ProductMigrationSource.objects.create(name="test")
        )
        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.delete(REST_PRODUCTMIGRATIONOPTION_DETAIL % 1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, "API endpoint is always read only"
        assert response.json() == {'detail': 'Method "DELETE" not allowed.'}
        assert ProductMigrationOption.objects.count() == 1, "no product migration option was deleted"

    def test_search_field(self):
        """
        search field contains a regular expression on the product id of the migration option and on the
        replacement product id
        :return:
        """
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 2,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 2
            },
            "data": [
                {
                    "migration_source": 1,
                    "migration_product_info_url": None,
                    "url": "http://testserver/productdb/api/v1/productmigrationoptions/%d/",
                    "replacement_product_id": "replacement",
                    "id": 1,
                    "product": 1,
                    "comment": "",
                },
                {
                    "migration_source": 1,
                    "migration_product_info_url": None,
                    "url": "http://testserver/productdb/api/v1/productmigrationoptions/%d/",
                    "replacement_product_id": "replacement2",
                    "id": 2,
                    "product": 2,
                    "comment": "",
                }
            ]
        }
        p1 = models.Product.objects.create(vendor=Vendor.objects.get(id=1), id=1, product_id="A1")
        p2 = models.Product.objects.create(vendor=Vendor.objects.get(id=1), id=2, product_id="A2")
        p3 = models.Product.objects.create(vendor=Vendor.objects.get(id=1), id=3, product_id="B1")
        pmg = models.ProductMigrationSource.objects.create(name="Cisco", id=1)

        pmo1 = models.ProductMigrationOption.objects.create(product=p1, migration_source=pmg,
                           replacement_product_id=expected_result["data"][0]["replacement_product_id"], comment="")
        pmo2 = models.ProductMigrationOption.objects.create(product=p2, migration_source=pmg,
                           replacement_product_id=expected_result["data"][1]["replacement_product_id"], comment="")
        models.ProductMigrationOption.objects.create(product=p3, migration_source=pmg,
                    replacement_product_id=expected_result["data"][1]["replacement_product_id"], comment="")
        expected_result["data"][0]["id"] = pmo1.id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % pmo1.id
        expected_result["data"][0]["comment"] = pmo1.comment
        expected_result["data"][1]["id"] = pmo2.id
        expected_result["data"][1]["url"] = expected_result["data"][1]["url"] % pmo2.id
        expected_result["data"][1]["comment"] = pmo2.comment

        client = APIClient()
        client.login(**AUTH_USER)
        # verify the use of regular expressions
        response = client.get(REST_PRODUCTMIGRATIONOPTION_LIST + "?search=" + quote("^A"))

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"

        assert jdata == expected_result, "unexpected result from API endpoint"

    def test_filter_fields(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 2,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 2
            },
            "data": [
                {
                    "migration_source": 1,
                    "migration_product_info_url": None,
                    "url": "http://testserver/productdb/api/v1/productmigrationoptions/%d/",
                    "replacement_product_id": "replacement1",
                    "id": 1,
                    "product": 1,
                    "comment": "",
                },
                {
                    "migration_source": 2,
                    "migration_product_info_url": None,
                    "url": "http://testserver/productdb/api/v1/productmigrationoptions/%d/",
                    "replacement_product_id": "replacement2",
                    "id": 2,
                    "product": 2,
                    "comment": "",
                }
            ]
        }
        p1 = models.Product.objects.create(vendor=Vendor.objects.get(id=1), id=1, product_id="A1")
        p2 = models.Product.objects.create(vendor=Vendor.objects.get(id=1), id=2, product_id="A2")
        p3 = models.Product.objects.create(vendor=Vendor.objects.get(id=1), id=3, product_id="B1")
        pmg = models.ProductMigrationSource.objects.create(name="Cisco", id=1)
        pmg2 = models.ProductMigrationSource.objects.create(name="Other", id=2)

        pmo1 = models.ProductMigrationOption.objects.create(product=p1, migration_source=pmg,
                           replacement_product_id=expected_result["data"][0]["replacement_product_id"], comment="")
        pmo2 = models.ProductMigrationOption.objects.create(product=p2, migration_source=pmg2,
                           replacement_product_id=expected_result["data"][1]["replacement_product_id"], comment="")
        models.ProductMigrationOption.objects.create(product=p3, migration_source=pmg2,
                    replacement_product_id=expected_result["data"][1]["replacement_product_id"], comment="")
        expected_result["data"][0]["id"] = pmo1.id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % pmo1.id
        expected_result["data"][0]["comment"] = pmo1.comment
        expected_result["data"][1]["id"] = pmo2.id
        expected_result["data"][1]["url"] = expected_result["data"][1]["url"] % pmo2.id
        expected_result["data"][1]["comment"] = pmo2.comment

        client = APIClient()
        client.login(**AUTH_USER)

        # use ID field filter (exact match)
        response = client.get(REST_PRODUCTMIGRATIONOPTION_LIST + "?id=%s" % pmo1.id)

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        mod_res = expected_result
        mod_res["pagination"] = {
            "page": 1,
            "page_records": 1,
            "url": {
                "next": None,
                "previous": None
            },
            "last_page": 1,
            "total_records": 1
        }
        del mod_res["data"][1]
        assert jdata == expected_result, "unexpected result from API endpoint"

        # use replacement_product_id field filter (startswith match)
        response = client.get(REST_PRODUCTMIGRATIONOPTION_LIST + "?replacement_product_id=" + quote("replacement1"))

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata == mod_res, "unexpected result from API endpoint"

        # use product field filter (startswith match)
        response = client.get(REST_PRODUCTMIGRATIONOPTION_LIST + "?product=" + quote("A1"))

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata == mod_res, "unexpected result from API endpoint"

        # use migration_source field filter (startswith match)
        response = client.get(REST_PRODUCTMIGRATIONOPTION_LIST + "?migration_source=" + quote("Cisco"))

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata == mod_res, "unexpected result from API endpoint"

        # call with empty result
        response = client.get(REST_PRODUCTMIGRATIONOPTION_LIST + "?replacement_product_id=" + quote("invalid"))

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 0, "should return nothing, because an exact match is required"


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
class TestProductMigrationSourceAPIEndpoint:
    """
    Django REST Framework API endpoint tests for the ProductMigrationSource model
    """
    def test_token_authentication(self, live_server):
        token, _ = Token.objects.get_or_create(user=User.objects.get(username=AUTH_USER["username"]))

        response = requests.get(live_server + REST_PRODUCTMIGRATIONSOURCE_LIST, headers={
            "Authorization": "Token %s" % token.key
        })

        assert response.status_code == status.HTTP_200_OK, response.text

        response = requests.get(live_server + REST_PRODUCTMIGRATIONSOURCE_LIST, headers={
            "Authorization": "Token invalid_token"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_read_access_with_authenticated_user(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 2,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 2
            },
            "data": [
                {
                    "id": 1,
                    "preference": 50,
                    "url": "http://testserver/productdb/api/v1/productmigrationsources/1/",
                    "description": "My description",
                    "name": "Cisco",
                },
                {
                    "id": 2,
                    "preference": 50,
                    "url": "http://testserver/productdb/api/v1/productmigrationsources/2/",
                    "description": "My other description",
                    "name": "other",
                }
            ]
        }

        [
            models.ProductMigrationSource.objects.create(**{
                x: y for x, y in expected_result["data"][i].items() if x != "url"
            }) for i in range(0, len(expected_result["data"]))
        ]

        client = APIClient()
        client.login(**AUTH_USER)
        response = client.get(REST_PRODUCTMIGRATIONSOURCE_LIST)

        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not found in result"
        assert jdata == expected_result, "unexpected result from API endpoint"

        # access first element of the list
        response = client.get(jdata["data"][0]["url"])

        assert response.status_code == status.HTTP_200_OK
        assert jdata["data"][0] == response.json()

    def test_add_access_with_permission(self):
        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="add_productmigrationsource")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.add_productmigrationsource")

        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.post(REST_PRODUCTMIGRATIONSOURCE_LIST, data={"name": "Awesome Product Migration Source"})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, "API endpoint is always read only"
        assert response.json() == {'detail': 'Method "POST" not allowed.'}
        assert ProductMigrationSource.objects.count() == 0, "no additional vendor is created"

    def test_change_access_with_permission(self):
        # create a user with permissions
        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="change_productmigrationsource")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.change_productmigrationsource")

        models.ProductMigrationSource.objects.create(name="foo")
        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.put(REST_PRODUCTMIGRATIONSOURCE_DETAIL % 1, data={"name": "renamed product migration source"})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, "API endpoint is always read only"
        assert response.json() == {'detail': 'Method "PUT" not allowed.'}

    def test_delete_access_with_permission(self):
        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="delete_productmigrationsource")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.delete_productmigrationsource")

        models.ProductMigrationSource.objects.create(name="source")
        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.delete(REST_PRODUCTMIGRATIONSOURCE_DETAIL % 1)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, "API endpoint is always read only"
        assert response.json() == {'detail': 'Method "DELETE" not allowed.'}
        assert ProductMigrationSource.objects.count() == 1, "no product migration source was deleted"

    def test_search_field(self):
        """
        search field implementation contains a regular expression search on the vendor name field
        :return:
        """
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "name": "Cisco Systems",
                    "url": "http://testserver/productdb/api/v1/productmigrationsources/%d/",
                    "id": 1,
                    "preference": 50,
                    "description": None,
                }
            ]
        }
        pmg= models.ProductMigrationSource.objects.create(name="Cisco Systems")
        expected_result["data"][0]["id"] = pmg.id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % pmg.id
        models.ProductMigrationSource.objects.create(name="Other PMG")

        client = APIClient()
        client.login(**AUTH_USER)
        # verify the use of regular expressions
        response = client.get(REST_PRODUCTMIGRATIONSOURCE_LIST + "?search=" + quote("^Ci"))

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata == expected_result, "unexpected result from API endpoint"

    def test_filter_fields(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "description": None,
                    "id": 1,
                    "name": "Cisco Systems",
                    "preference": 50,
                    "url": "http://testserver/productdb/api/v1/productmigrationsources/%d/"
                }
            ]
        }
        pmg= models.ProductMigrationSource.objects.create(name="Cisco Systems")
        expected_result["data"][0]["id"] = pmg.id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % pmg.id
        models.ProductMigrationSource.objects.create(name="Other PMG")

        client = APIClient()
        client.login(**AUTH_USER)

        # use ID field filter (exact match)
        response = client.get(REST_PRODUCTMIGRATIONSOURCE_LIST + "?id=%s" % pmg.id)

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata == expected_result, "unexpected result from API endpoint"

        # use name field filter (exact match)
        response = client.get(REST_PRODUCTMIGRATIONSOURCE_LIST + "?name=" + quote("Cisco Systems"))

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata == expected_result, "unexpected result from API endpoint"

        # call with empty result
        response = client.get(REST_PRODUCTMIGRATIONSOURCE_LIST + "?name=" + quote("Cisco"))

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 0, "should return nothing, because an exact match is required"


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
class TestProductGroupAPIEndpoint:
    """Django REST Framework API endpoint tests for the Product Group model"""
    def test_token_authentication(self, live_server):
        token, _ = Token.objects.get_or_create(user=User.objects.get(username=AUTH_USER["username"]))

        response = requests.get(live_server + REST_PRODUCT_GROUP_LIST, headers={
            "Authorization": "Token %s" % token.key
        })

        assert response.status_code == status.HTTP_200_OK, response.text

        response = requests.get(live_server + REST_PRODUCT_GROUP_LIST, headers={
            "Authorization": "Token invalid_token"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_read_access_with_authenticated_user(self):
        expected_result = {
            "data": [
                {
                    "url": "http://testserver/productdb/api/v1/productgroups/1/",
                    "name": "product group 1",
                    "id": 1,
                    "vendor": 0
                },
                {
                    "url": "http://testserver/productdb/api/v1/productgroups/2/",
                    "name": "product group 2",
                    "id": 2,
                    "vendor": 0
                },
                {
                    "url": "http://testserver/productdb/api/v1/productgroups/3/",
                    "name": "product group 3",
                    "id": 3,
                    "vendor": 0
                }
            ],
            "pagination": {
                "page_records": 3,
                "last_page": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "page": 1,
                "total_records": 3
            }
        }

        models.ProductGroup.objects.create(name="product group 1")
        models.ProductGroup.objects.create(name="product group 2")
        models.ProductGroup.objects.create(name="product group 3")

        client = APIClient()
        client.login(**AUTH_USER)
        response = client.get(REST_PRODUCT_GROUP_LIST)
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not found in result"
        # adjust ID values from Database
        for c in range(0, 3):
            expected_result["data"][c]["id"] = ProductGroup.objects.get(name="product group %d" % (c+1)).id
            expected_result["data"][c]["url"] = "http://testserver/productdb/api/v1/productgroups/%d/" % expected_result["data"][c]["id"]
        assert jdata == expected_result, "unexpected result from API endpoint"

        # access first element of the list
        response = client.get(jdata["data"][0]["url"])

        assert response.status_code == status.HTTP_200_OK
        assert jdata["data"][0] == response.json()

    def test_add_access_with_permission(self):
        test_user = "user"
        test_product_group_name = "Test Product Group"
        expected_result = {
            "vendor": 1,
            "name": test_product_group_name,
            "url": "http://testserver/productdb/api/v1/productgroups/1/",
            "id": 1
        }

        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="add_productgroup")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.add_productgroup")

        client = APIClient()
        client.login(username=test_user, password=test_user)

        # create with name
        response = client.post(REST_PRODUCT_GROUP_LIST, data={"name": test_product_group_name})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'vendor': ['This field is required.']}

        # create with name name and Vendor ID
        response = client.post(REST_PRODUCT_GROUP_LIST, data={"name": test_product_group_name, "vendor": 1})

        assert response.status_code == status.HTTP_201_CREATED
        # adjust ID values from Database
        expected_result["id"] = ProductGroup.objects.get(name=test_product_group_name).id
        expected_result["url"] = "http://testserver/productdb/api/v1/productgroups/%d/" % expected_result["id"]
        assert response.json() == expected_result, "Should provide the new product group"

    def test_change_access_with_permission(self):
        test_product_group = "renamed product group"
        pg = models.ProductGroup.objects.create(name="product group")
        expected_result = {
            "url": "http://testserver/productdb/api/v1/productgroups/%d/",
            "vendor": 0,
            "name": test_product_group,
            "id": 0
        }

        # create a user with permissions
        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="change_productgroup")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.change_productgroup")

        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.put(REST_PRODUCT_GROUP_DETAIL % pg.id, data={"name": test_product_group})

        assert response.status_code == status.HTTP_200_OK
        # adjust pk value
        expected_result["id"] = ProductGroup.objects.get(name=test_product_group).id
        expected_result["url"] = expected_result["url"] % expected_result["id"]
        assert response.json() == expected_result

    def test_delete_access_with_permission(self):
        pg = models.ProductGroup.objects.create(name="Foo")
        assert ProductGroup.objects.count() == 1

        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="delete_productgroup")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.delete_productgroup")

        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.delete(REST_PRODUCT_GROUP_DETAIL % pg.id)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert ProductGroup.objects.count() == 0

    def test_count_endpoint(self):
        models.ProductGroup.objects.create(name="product group 1")
        models.ProductGroup.objects.create(name="product group 2")
        models.ProductGroup.objects.create(name="product group 3")
        assert ProductGroup.objects.count() == 3

        client = APIClient()
        client.login(**AUTH_USER)
        response = client.get(REST_PRODUCT_GROUP_COUNT)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'count': 3}

    def test_search_field(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 5,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 5
            },
            "data": [
                {
                    "vendor": 0,
                    "id": 0,
                    "name": "product group 0",
                    "url": "http://testserver/productdb/api/v1/productgroups/%d/"
                },
                {
                    "vendor": 0,
                    "id": 0,
                    "name": "product group 1",
                    "url": "http://testserver/productdb/api/v1/productgroups/%d/"
                },
                {
                    "vendor": 0,
                    "id": 0,
                    "name": "product group 2",
                    "url": "http://testserver/productdb/api/v1/productgroups/%d/"
                },
                {
                    "vendor": 0,
                    "id": 0,
                    "name": "product group 3",
                    "url": "http://testserver/productdb/api/v1/productgroups/%d/"
                },
                {
                    "vendor": 0,
                    "id": 0,
                    "name": "product group 4",
                    "url": "http://testserver/productdb/api/v1/productgroups/%d/"
                }
            ]
        }
        for e in range(0, 5):
            ProductGroup.objects.create(name="product group %d" % e)

        client = APIClient()
        client.login(**AUTH_USER)
        # verify the use of regular expressions
        response = client.get(REST_PRODUCT_GROUP_LIST + "?search=" + quote("^product group \d+$"))
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 5, "Should contain five elements"

        # adjust pk values
        for e in range(0, 5):
            expected_result["data"][e]["id"] = ProductGroup.objects.get(name="product group %d" % e).id
            expected_result["data"][e]["url"] = expected_result["data"][e]["url"] % expected_result["data"][e]["id"]

        assert jdata == expected_result, "unexpected result from API endpoint"

    def test_filter_id_field(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "vendor": 0,
                    "id": 1,
                    "name": "TBD",
                    "url": "http://testserver/productdb/api/v1/productgroups/%d/"
                },
            ]
        }
        pg = models.ProductGroup.objects.create(vendor=Vendor.objects.get(id=1), name="test group")
        expected_result["data"][0]["id"] = pg.id
        expected_result["data"][0]["vendor"] = pg.vendor.id
        expected_result["data"][0]["name"] = pg.name
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % expected_result["data"][0]["id"]
        assert ProductGroup.objects.count() == 1

        client = APIClient()
        client.login(**AUTH_USER)

        # use ID field filter (exact match)
        response = client.get(REST_PRODUCT_GROUP_LIST + "?id=%d" % pg.id)
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 1, "Expect a single entry in the result"
        assert jdata == expected_result, "unexpected result from API endpoint"

    def test_filter_name_field(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "vendor": 0,
                    "id": 1,
                    "name": "",
                    "url": "http://testserver/productdb/api/v1/productgroups/%d/"
                },
            ]
        }
        pg = models.ProductGroup.objects.create(vendor=Vendor.objects.get(id=1), name="test group")
        expected_result["data"][0]["id"] = pg.id
        expected_result["data"][0]["vendor"] = pg.vendor.id
        expected_result["data"][0]["name"] = pg.name
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % expected_result["data"][0]["id"]
        assert ProductGroup.objects.count() == 1

        client = APIClient()
        client.login(**AUTH_USER)

        # use name field (exact match)
        response = client.get(REST_PRODUCT_GROUP_LIST + "?name=" + quote(pg.name))
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 1, "Expect a single entry in the result"
        assert jdata == expected_result, "unexpected result from API endpoint"

    def test_filter_vendor_field(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "vendor": 0,
                    "id": 1,
                    "name": "TBD",
                    "url": "http://testserver/productdb/api/v1/productgroups/%d/"
                },
            ]
        }
        pg = models.ProductGroup.objects.create(vendor=Vendor.objects.get(id=1), name="test group")
        expected_result["data"][0]["id"] = pg.id
        expected_result["data"][0]["vendor"] = pg.vendor.id
        expected_result["data"][0]["name"] = pg.name
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % expected_result["data"][0]["id"]
        assert ProductGroup.objects.count() == 1

        client = APIClient()
        client.login(**AUTH_USER)

        # use vendor field (startswith)
        response = client.get(REST_PRODUCT_GROUP_LIST + "?vendor=" + quote("Cisco"))
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 1, "Expect a single entry in the result"
        assert jdata == expected_result, "unexpected result from API endpoint"


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
class TestProductAPIEndpoint:
    """Django REST Framework API endpoint tests for the Product model"""
    today_string = DateFormat(datetime.now()).format(get_format(settings.SHORT_DATE_FORMAT))

    def test_token_authentication(self, live_server):
        token, _ = Token.objects.get_or_create(user=User.objects.get(username=AUTH_USER["username"]))

        response = requests.get(live_server + REST_PRODUCT_LIST, headers={
            "Authorization": "Token %s" % token.key
        })

        assert response.status_code == status.HTTP_200_OK, response.text

        response = requests.get(live_server + REST_PRODUCT_LIST, headers={
            "Authorization": "Token invalid_token"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_read_access_with_authenticated_user(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "id": 0,
                    "list_price": "12.32",
                    "description": "",
                    "eol_reference_url": None,
                    "eol_ext_announcement_date": None,
                    "url": "http://testserver/productdb/api/v1/products/%d/",
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "eol_reference_number": None,
                    "end_of_sw_maintenance_date": None,
                    "tags": "",
                    "vendor": 0,
                    "product_id": "",
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "eox_update_time_stamp": None,
                    "product_group": None,
                    "end_of_new_service_attachment_date": None,
                    "currency": "USD",
                    "lc_state_sync": False,
                    "internal_product_id": None,
                    "update_timestamp": self.today_string,
                    "list_price_timestamp": self.today_string
                }
            ]
        }
        p = models.Product.objects.create(product_id="A")
        # list price timestamp not set with create
        p.list_price = 12.32
        p.save()
        expected_result["data"][0]["id"] = p.id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % p.id
        expected_result["data"][0]["product_id"] = p.product_id

        client = APIClient()
        client.login(**AUTH_USER)

        response = client.get(REST_PRODUCT_LIST)
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not found in result"
        assert jdata["pagination"]["total_records"] == 1, "unexpected result from API endpoint"
        assert jdata == expected_result, "unexpected result from API endpoint"

        # access first element of the list
        response = client.get(jdata["data"][0]["url"])

        assert response.status_code == status.HTTP_200_OK
        assert jdata["data"][0] == response.json()

    def test_add_access_with_permission(self):
        v = Vendor.objects.create(name="test vendor")

        test_user = "user"
        test_product_id = "Test Product ID"
        expected_result = {
            "currency": "USD",
            "end_of_service_contract_renewal": None,
            "eol_reference_url": None,
            "url": "http://testserver/productdb/api/v1/products/%d/",
            "eol_reference_number": None,
            "product_group": None,
            "end_of_sale_date": None,
            "description": "",
            "vendor": v.id,
            "tags": "",
            "list_price": None,
            "eol_ext_announcement_date": None,
            "eox_update_time_stamp": None,
            "end_of_new_service_attachment_date": None,
            "end_of_support_date": None,
            "end_of_sw_maintenance_date": None,
            "end_of_sec_vuln_supp_date": None,
            "end_of_routine_failure_analysis": None,
            "id": 0,
            "product_id": test_product_id,
            "lc_state_sync": False,
            "internal_product_id": None,
            "update_timestamp": self.today_string,
            "list_price_timestamp": None
        }

        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="add_product")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.add_product")

        client = APIClient()
        client.login(username=test_user, password=test_user)

        # create with name
        response = client.post(REST_PRODUCT_LIST, data={"product_id": test_product_id, "vendor": v.id})

        assert response.status_code == status.HTTP_201_CREATED, response.content.decode()
        # adjust ID values from Database
        expected_result["id"] = Product.objects.get(product_id=test_product_id, vendor=v).id
        expected_result["url"] = "http://testserver/productdb/api/v1/products/%d/" % expected_result["id"]
        assert response.json() == expected_result, "Should provide the new product"

    def test_create_product_with_lc_state_sync_field(self):
        v = Vendor.objects.create(name="test vendor")

        test_user = "user"
        test_product_id = "Test Product ID"
        expected_result = {
            "currency": "USD",
            "end_of_service_contract_renewal": None,
            "eol_reference_url": None,
            "url": "http://testserver/productdb/api/v1/products/%d/",
            "eol_reference_number": None,
            "product_group": None,
            "end_of_sale_date": None,
            "description": "",
            "vendor": v.id,
            "tags": "",
            "list_price": None,
            "eol_ext_announcement_date": None,
            "eox_update_time_stamp": None,
            "end_of_new_service_attachment_date": None,
            "end_of_support_date": None,
            "end_of_sw_maintenance_date": None,
            "end_of_sec_vuln_supp_date": None,
            "end_of_routine_failure_analysis": None,
            "id": 0,
            "product_id": test_product_id,
            "lc_state_sync": False,
            "internal_product_id": None,
            "update_timestamp": self.today_string,
            "list_price_timestamp": None
        }

        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="add_product")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.add_product")

        client = APIClient()
        client.login(username=test_user, password=test_user)

        # create with name
        response = client.post(REST_PRODUCT_LIST, data={
            "product_id": test_product_id,
            "vendor": v.id,
            "lc_state_sync": True
        })

        assert response.status_code == status.HTTP_201_CREATED
        # adjust ID values from Database
        expected_result["id"] = Product.objects.get(product_id=test_product_id).id
        expected_result["url"] = "http://testserver/productdb/api/v1/products/%d/" % expected_result["id"]
        from pprint import pprint
        pprint(response.json())
        assert response.json() == expected_result, "Should provide the new product"

    def test_change_lc_state_sync(self):
        p= models.Product.objects.create(product_id="product ID")
        expected_result = {
            "currency": "USD",
            "end_of_service_contract_renewal": None,
            "eol_reference_url": None,
            "url": "http://testserver/productdb/api/v1/products/%d/",
            "eol_reference_number": None,
            "product_group": None,
            "end_of_sale_date": None,
            "description": "",
            "vendor": 0,
            "tags": "",
            "list_price": None,
            "eol_ext_announcement_date": None,
            "eox_update_time_stamp": None,
            "end_of_new_service_attachment_date": None,
            "end_of_support_date": None,
            "end_of_sw_maintenance_date": None,
            "end_of_sec_vuln_supp_date": None,
            "end_of_routine_failure_analysis": None,
            "id": 0,
            "product_id": p.product_id,
            "lc_state_sync": False,
            "internal_product_id": None,
            "update_timestamp": self.today_string,
            "list_price_timestamp": None
        }

        # create a user with permissions
        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        perm = Permission.objects.get(codename="change_product")
        assert perm is not None
        u.user_permissions.add(perm)
        u.save()
        assert u.has_perm("productdb.change_product")

        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.put(REST_PRODUCT_DETAIL % p.id, data={
            "product_id": p.product_id,
            "lc_state_sync": True
        })

        assert response.status_code == status.HTTP_200_OK
        # adjust pk value
        expected_result["id"] = Product.objects.get(product_id="product ID").id
        expected_result["url"] = expected_result["url"] % expected_result["id"]
        assert response.json() == expected_result

    def test_change_access_with_permission(self):
        p= models.Product.objects.create(product_id="product ID")
        test_renamed_product = "renamed product"
        expected_result = {
            "currency": "USD",
            "end_of_service_contract_renewal": None,
            "eol_reference_url": None,
            "url": "http://testserver/productdb/api/v1/products/%d/",
            "eol_reference_number": None,
            "product_group": None,
            "end_of_sale_date": None,
            "description": "",
            "vendor": 0,
            "tags": "",
            "list_price": None,
            "eol_ext_announcement_date": None,
            "eox_update_time_stamp": None,
            "end_of_new_service_attachment_date": None,
            "end_of_support_date": None,
            "end_of_sw_maintenance_date": None,
            "end_of_sec_vuln_supp_date": None,
            "end_of_routine_failure_analysis": None,
            "id": 0,
            "product_id": test_renamed_product,
            "lc_state_sync": False,
            "internal_product_id": None,
            "update_timestamp": self.today_string,
            "list_price_timestamp": None
        }

        # create a user with permissions
        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        perm = Permission.objects.get(codename="change_product")
        assert perm is not None
        u.user_permissions.add(perm)
        u.save()
        assert u.has_perm("productdb.change_product")

        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.put(REST_PRODUCT_DETAIL % p.id, data={"product_id": test_renamed_product})

        assert response.status_code == status.HTTP_200_OK
        # adjust pk value
        expected_result["id"] = Product.objects.get(product_id=test_renamed_product).id
        expected_result["url"] = expected_result["url"] % expected_result["id"]
        assert response.json() == expected_result

    def test_change_product_group(self):
        v1 = Vendor.objects.get(id=1)
        v2 = Vendor.objects.get(id=2)
        invalid_pg = models.ProductGroup.objects.create(name="invalid product group", vendor=v2)
        valid_pg = models.ProductGroup.objects.create(name="valid product group", vendor=v1)
        p= models.Product.objects.create(product_id="product ID", vendor=v1)
        expected_result = {
            "currency": "USD",
            "end_of_service_contract_renewal": None,
            "eol_reference_url": None,
            "url": "http://testserver/productdb/api/v1/products/%d/" % p.id,
            "eol_reference_number": None,
            "product_group": valid_pg.id,
            "end_of_sale_date": None,
            "description": "",
            "vendor": v1.id,
            "tags": "",
            "list_price": None,
            "eol_ext_announcement_date": None,
            "eox_update_time_stamp": None,
            "end_of_new_service_attachment_date": None,
            "end_of_support_date": None,
            "end_of_sw_maintenance_date": None,
            "end_of_sec_vuln_supp_date": None,
            "end_of_routine_failure_analysis": None,
            "id": p.id,
            "product_id": p.product_id,
            "lc_state_sync": False,
            "internal_product_id": None,
            "update_timestamp": self.today_string,
            "list_price_timestamp": None
        }

        client = APIClient()
        client.login(**SUPER_USER)

        # try to associate the product to a product group of a different vendor
        response = client.put(REST_PRODUCT_DETAIL % p.id, data={
            "product_id": p.product_id,
            "product_group": invalid_pg.id
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        jdata = response.json()
        assert len(jdata) == 1, "Should contain a single error message"
        assert "product_group" in jdata
        assert "Invalid product group, group and product must be associated to the same vendor" in str(jdata)

        # try to associate the product to a product group of the same vendor
        response = client.put(REST_PRODUCT_DETAIL % p.id, data={
            "product_id": p.product_id,
            "product_group": valid_pg.id
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_result

    def test_delete_access_with_permission(self):
        p = models.Product.objects.create(product_id="test")
        assert Product.objects.count() == 1

        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        perm = Permission.objects.get(codename="delete_product")
        assert perm is not None
        u.user_permissions.add(perm)
        u.save()
        assert u.has_perm("productdb.delete_product")

        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.delete(REST_PRODUCT_DETAIL % p.id)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Product.objects.count() == 0

    def test_count_endpoint(self):
        models.Product.objects.create(product_id="product 1")
        models.Product.objects.create(product_id="product 2")
        models.Product.objects.create(product_id="product 3")
        assert Product.objects.count() == 3

        client = APIClient()
        client.login(**AUTH_USER)
        response = client.get(REST_PRODUCT_COUNT)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'count': 3}

    def test_search_field_by_product_id(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 2,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 2
            },
            "data": [
                {
                    "id": 0,
                    "list_price": None,
                    "description": "",
                    "eol_reference_url": None,
                    "eol_ext_announcement_date": None,
                    "url": "http://testserver/productdb/api/v1/products/%d/",
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "eol_reference_number": None,
                    "end_of_sw_maintenance_date": None,
                    "tags": "",
                    "vendor": 0,
                    "product_id": "product 21",
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "eox_update_time_stamp": None,
                    "product_group": None,
                    "end_of_new_service_attachment_date": None,
                    "currency": "USD",
                    "lc_state_sync": False,
                    "internal_product_id": None,
                    "update_timestamp": self.today_string,
                    "list_price_timestamp": None
                },
                {
                    "id": 0,
                    "list_price": None,
                    "description": "",
                    "eol_reference_url": None,
                    "eol_ext_announcement_date": None,
                    "url": "http://testserver/productdb/api/v1/products/%d/",
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "eol_reference_number": None,
                    "end_of_sw_maintenance_date": None,
                    "tags": "",
                    "vendor": 0,
                    "product_id": "product 22",
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "eox_update_time_stamp": None,
                    "product_group": None,
                    "end_of_new_service_attachment_date": None,
                    "currency": "USD",
                    "lc_state_sync": False,
                    "internal_product_id": None,
                    "update_timestamp": self.today_string,
                    "list_price_timestamp": None
                }
            ]
        }
        for e in range(0, 5):
            Product.objects.create(product_id="test product %d" % e)
        for e in range(1, 3):
            p = Product.objects.create(product_id="product 2%d" % e)
            expected_result["data"][e-1]["id"] = p.id
            expected_result["data"][e-1]["url"] = expected_result["data"][e-1]["url"] % p.id

        client = APIClient()
        client.login(**AUTH_USER)
        # search by product ID (with regular expression
        response = client.get(REST_PRODUCT_LIST + "?search=" + quote("^product \d+$"))
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == len(expected_result["data"]), \
            "Should contain the same amount of elements as the expected result"

        assert jdata == expected_result, "unexpected result from API endpoint"

    def test_search_field_by_product_description(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 2,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 2
            },
            "data": [
                {
                    "id": 0,
                    "list_price": None,
                    "description": "my search description",
                    "eol_reference_url": None,
                    "eol_ext_announcement_date": None,
                    "url": "http://testserver/productdb/api/v1/products/%d/",
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "eol_reference_number": None,
                    "end_of_sw_maintenance_date": None,
                    "tags": "",
                    "vendor": 0,
                    "product_id": "product 21",
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "eox_update_time_stamp": None,
                    "product_group": None,
                    "end_of_new_service_attachment_date": None,
                    "currency": "USD",
                    "lc_state_sync": False,
                    "internal_product_id": None,
                    "update_timestamp": self.today_string,
                    "list_price_timestamp": None
                },
                {
                    "id": 0,
                    "list_price": None,
                    "description": "other search description",
                    "eol_reference_url": None,
                    "eol_ext_announcement_date": None,
                    "url": "http://testserver/productdb/api/v1/products/%d/",
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "eol_reference_number": None,
                    "end_of_sw_maintenance_date": None,
                    "tags": "",
                    "vendor": 0,
                    "product_id": "product 22",
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "eox_update_time_stamp": None,
                    "product_group": None,
                    "end_of_new_service_attachment_date": None,
                    "currency": "USD",
                    "lc_state_sync": False,
                    "internal_product_id": None,
                    "update_timestamp": self.today_string,
                    "list_price_timestamp": None
                }
            ]
        }
        for e in range(0, 5):
            Product.objects.create(product_id="test product %d" % e, description=str(e))

        for e in range(1, 3):
            p = Product.objects.create(
                product_id="product 2%d" % e,
                description=expected_result["data"][e-1]["description"]
            )
            expected_result["data"][e-1]["id"] = p.id
            expected_result["data"][e-1]["url"] = expected_result["data"][e-1]["url"] % p.id

        client = APIClient()
        client.login(**AUTH_USER)
        # search by product ID (with regular expression
        response = client.get(REST_PRODUCT_LIST + "?search=" + quote("^\w+ search description$"))
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == len(expected_result["data"]), \
            "Should contain the same amount of elements as the expected result"

        assert jdata == expected_result, "unexpected result from API endpoint"

    def test_filter_id_field(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "id": 0,
                    "list_price": None,
                    "description": "",
                    "eol_reference_url": None,
                    "eol_ext_announcement_date": None,
                    "url": "http://testserver/productdb/api/v1/products/%d/",
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "eol_reference_number": None,
                    "end_of_sw_maintenance_date": None,
                    "tags": "",
                    "vendor": 0,
                    "product_id": "product 22",
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "eox_update_time_stamp": None,
                    "product_group": None,
                    "end_of_new_service_attachment_date": None,
                    "currency": "USD",
                    "lc_state_sync": False,
                    "internal_product_id": None,
                    "update_timestamp": self.today_string,
                    "list_price_timestamp": None
                }
            ]
        }
        models.Product.objects.create(product_id="test", vendor=Vendor.objects.get(id=1))
        p = models.Product.objects.create(product_id="A", vendor=Vendor.objects.get(id=1))
        expected_result["data"][0]["id"] = p.id
        expected_result["data"][0]["vendor"] = p.vendor.id
        expected_result["data"][0]["product_id"] = p.product_id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % expected_result["data"][0]["id"]
        assert Product.objects.count() == 2

        client = APIClient()
        client.login(**AUTH_USER)

        # use vendor field (startswith)
        response = client.get(REST_PRODUCT_LIST + "?id=" + str(p.id))
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 1, "Expect a single entry in the result"
        assert jdata == expected_result, "unexpected result from API endpoint"

    def test_filter_product_id_field(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "id": 0,
                    "list_price": None,
                    "description": "",
                    "eol_reference_url": None,
                    "eol_ext_announcement_date": None,
                    "url": "http://testserver/productdb/api/v1/products/%d/",
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "eol_reference_number": None,
                    "end_of_sw_maintenance_date": None,
                    "tags": "",
                    "vendor": 0,
                    "product_id": "product 22",
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "eox_update_time_stamp": None,
                    "product_group": None,
                    "end_of_new_service_attachment_date": None,
                    "currency": "USD",
                    "lc_state_sync": False,
                    "internal_product_id": None,
                    "update_timestamp": self.today_string,
                    "list_price_timestamp": None
                }
            ]
        }
        models.Product.objects.create(vendor=Vendor.objects.get(id=1), product_id="AAAAAAAAAA")
        p = models.Product.objects.create(vendor=Vendor.objects.get(id=1), product_id="BBBBBBBBBB")
        expected_result["data"][0]["id"] = p.id
        expected_result["data"][0]["vendor"] = p.vendor.id
        expected_result["data"][0]["product_id"] = p.product_id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % expected_result["data"][0]["id"]
        assert Product.objects.count() == 2

        client = APIClient()
        client.login(**AUTH_USER)

        # use product_id (exact match)
        response = client.get(REST_PRODUCT_LIST + "?product_id=" + quote(p.product_id))
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 1, "Expect a single entry in the result"
        assert jdata == expected_result, "unexpected result from API endpoint"

        # use incomplete product_id
        response = client.get(REST_PRODUCT_LIST + "?product_id=" + quote(p.product_id[:5]))
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 0, "Should return no element"

    def test_filter_vendor__name_field(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "id": 0,
                    "list_price": None,
                    "description": "",
                    "eol_reference_url": None,
                    "eol_ext_announcement_date": None,
                    "url": "http://testserver/productdb/api/v1/products/%d/",
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "eol_reference_number": None,
                    "end_of_sw_maintenance_date": None,
                    "tags": "",
                    "vendor": 0,
                    "product_id": "product 22",
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "eox_update_time_stamp": None,
                    "product_group": None,
                    "end_of_new_service_attachment_date": None,
                    "currency": "USD",
                    "lc_state_sync": False,
                    "internal_product_id": None,
                    "update_timestamp": self.today_string,
                    "list_price_timestamp": None
                }
            ]
        }
        models.Product.objects.create(vendor=Vendor.objects.get(id=2), product_id="A")
        p = models.Product.objects.create(vendor=Vendor.objects.get(id=1), product_id="B")
        expected_result["data"][0]["id"] = p.id
        expected_result["data"][0]["vendor"] = p.vendor.id
        expected_result["data"][0]["product_id"] = p.product_id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % expected_result["data"][0]["id"]
        assert Product.objects.count() == 2

        client = APIClient()
        client.login(**AUTH_USER)

        # use vendor field (startswith)
        response = client.get(REST_PRODUCT_LIST + "?vendor__name=" + quote("Cisco"))
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 1, "Expect a single entry in the result"
        assert jdata == expected_result, "unexpected result from API endpoint"

    def test_filter_vendor__id_field(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "id": 0,
                    "list_price": None,
                    "description": "",
                    "eol_reference_url": None,
                    "eol_ext_announcement_date": None,
                    "url": "http://testserver/productdb/api/v1/products/%d/",
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "eol_reference_number": None,
                    "end_of_sw_maintenance_date": None,
                    "tags": "",
                    "vendor": 0,
                    "product_id": "product 22",
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "eox_update_time_stamp": None,
                    "product_group": None,
                    "end_of_new_service_attachment_date": None,
                    "currency": "USD",
                    "lc_state_sync": False,
                    "internal_product_id": None,
                    "update_timestamp": self.today_string,
                    "list_price_timestamp": None
                }
            ]
        }
        models.Product.objects.create(vendor=Vendor.objects.get(id=2), product_id="A")
        p = models.Product.objects.create(vendor=Vendor.objects.get(id=1), product_id="B")
        expected_result["data"][0]["id"] = p.id
        expected_result["data"][0]["vendor"] = p.vendor.id
        expected_result["data"][0]["product_id"] = p.product_id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % expected_result["data"][0]["id"]
        assert Product.objects.count() == 2

        client = APIClient()
        client.login(**AUTH_USER)

        # use vendor field (startswith)
        v = Vendor.objects.get(name__startswith="Cisco")
        response = client.get(REST_PRODUCT_LIST + "?vendor__id=%s" % v.id)
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 1, "Expect a single entry in the result"
        assert jdata == expected_result, "unexpected result from API endpoint"

    def test_filter_vendor_field(self):
        """DEPRECATED, filter will be removed in later versions"""
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "id": 0,
                    "list_price": None,
                    "description": "",
                    "eol_reference_url": None,
                    "eol_ext_announcement_date": None,
                    "url": "http://testserver/productdb/api/v1/products/%d/",
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "eol_reference_number": None,
                    "end_of_sw_maintenance_date": None,
                    "tags": "",
                    "vendor": 0,
                    "product_id": "product 22",
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "eox_update_time_stamp": None,
                    "product_group": None,
                    "end_of_new_service_attachment_date": None,
                    "currency": "USD",
                    "lc_state_sync": False,
                    "internal_product_id": None,
                    "update_timestamp": self.today_string,
                    "list_price_timestamp": None
                }
            ]
        }
        models.Product.objects.create(vendor=Vendor.objects.get(id=2), product_id="B")
        p = models.Product.objects.create(vendor=Vendor.objects.get(id=1), product_id="A")
        expected_result["data"][0]["id"] = p.id
        expected_result["data"][0]["vendor"] = p.vendor.id
        expected_result["data"][0]["product_id"] = p.product_id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % expected_result["data"][0]["id"]
        assert Product.objects.count() == 2

        client = APIClient()
        client.login(**AUTH_USER)

        # use vendor field (startswith)
        response = client.get(REST_PRODUCT_LIST + "?vendor=" + quote("Cisco"))
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 1, "Expect a single entry in the result"
        assert jdata == expected_result, "unexpected result from API endpoint"

    def test_filter_product_group_field(self):
        """DEPRECATED, filter will be removed in later versions"""
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "id": 0,
                    "list_price": None,
                    "description": "",
                    "eol_reference_url": None,
                    "eol_ext_announcement_date": None,
                    "url": "http://testserver/productdb/api/v1/products/%d/",
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "eol_reference_number": None,
                    "end_of_sw_maintenance_date": None,
                    "tags": "",
                    "vendor": 0,
                    "product_id": "product 22",
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "eox_update_time_stamp": None,
                    "product_group": None,
                    "end_of_new_service_attachment_date": None,
                    "currency": "USD",
                    "lc_state_sync": False,
                    "internal_product_id": None,
                    "update_timestamp": self.today_string,
                    "list_price_timestamp": None
                }
            ]
        }
        v1 = Vendor.objects.get(id=1)
        v2 = Vendor.objects.get(id=2)
        models.Product.objects.create(
            product_id="A",
            vendor=v2,
            product_group=models.ProductGroup.objects.create(vendor=v2, name="PG")
        )
        pg = models.ProductGroup.objects.create(vendor=v1, name="TestPG")
        p = models.Product.objects.create(vendor=v1, product_group=pg, product_id="AAAAAAAA")
        expected_result["data"][0]["id"] = p.id
        expected_result["data"][0]["vendor"] = p.vendor.id
        expected_result["data"][0]["product_id"] = p.product_id
        expected_result["data"][0]["product_group"] = pg.id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % expected_result["data"][0]["id"]
        assert Product.objects.count() == 2

        client = APIClient()
        client.login(**AUTH_USER)

        # use product_group field (exact match)
        response = client.get(REST_PRODUCT_LIST + "?product_group=" + quote(pg.name))
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 1, "Expect a single entry in the result"
        assert jdata == expected_result, "unexpected result from API endpoint"

        # use incomplete product_group field
        response = client.get(REST_PRODUCT_LIST + "?product_group=" + quote(pg.name[:5]))
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 0, "Should return no element"

    def test_filter_product_group__name_field(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "id": 0,
                    "list_price": None,
                    "description": "",
                    "eol_reference_url": None,
                    "eol_ext_announcement_date": None,
                    "url": "http://testserver/productdb/api/v1/products/%d/",
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "eol_reference_number": None,
                    "end_of_sw_maintenance_date": None,
                    "tags": "",
                    "vendor": 0,
                    "product_id": "product 22",
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "eox_update_time_stamp": None,
                    "product_group": None,
                    "end_of_new_service_attachment_date": None,
                    "currency": "USD",
                    "lc_state_sync": False,
                    "internal_product_id": None,
                    "update_timestamp": self.today_string,
                    "list_price_timestamp": None
                }
            ]
        }
        v1 = Vendor.objects.get(id=1)
        v2 = Vendor.objects.get(id=2)
        models.Product.objects.create(
            product_id="A",
            vendor=v2,
            product_group=models.ProductGroup.objects.create(vendor=v2, name="PG")
        )
        pg = models.ProductGroup.objects.create(vendor=v1, name="TestPG")
        p = models.Product.objects.create(vendor=v1, product_group=pg, product_id="AAAAAAAAAA")
        expected_result["data"][0]["id"] = p.id
        expected_result["data"][0]["vendor"] = p.vendor.id
        expected_result["data"][0]["product_id"] = p.product_id
        expected_result["data"][0]["product_group"] = pg.id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % expected_result["data"][0]["id"]
        assert Product.objects.count() == 2

        client = APIClient()
        client.login(**AUTH_USER)

        # use product_group field (exact match)
        response = client.get(REST_PRODUCT_LIST + "?product_group__name=" + quote(pg.name))
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 1, "Expect a single entry in the result"
        assert jdata == expected_result, "unexpected result from API endpoint"

        # use incomplete product_group field
        response = client.get(REST_PRODUCT_LIST + "?product_group__name=" + quote(pg.name[:5]))
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 0, "Should return no element"

    def test_filter_product_group__id_field(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "id": 0,
                    "list_price": None,
                    "description": "",
                    "eol_reference_url": None,
                    "eol_ext_announcement_date": None,
                    "url": "http://testserver/productdb/api/v1/products/%d/",
                    "end_of_sec_vuln_supp_date": None,
                    "end_of_service_contract_renewal": None,
                    "end_of_support_date": None,
                    "eol_reference_number": None,
                    "end_of_sw_maintenance_date": None,
                    "tags": "",
                    "vendor": 0,
                    "product_id": "product 22",
                    "end_of_routine_failure_analysis": None,
                    "end_of_sale_date": None,
                    "eox_update_time_stamp": None,
                    "product_group": None,
                    "end_of_new_service_attachment_date": None,
                    "currency": "USD",
                    "lc_state_sync": False,
                    "internal_product_id": None,
                    "update_timestamp": self.today_string,
                    "list_price_timestamp": None
                }
            ]
        }
        v1 = Vendor.objects.get(id=1)
        v2 = Vendor.objects.get(id=2)
        models.Product.objects.create(
            product_id="A",
            vendor=v2,
            product_group=models.ProductGroup.objects.create(vendor=v2, name="PG")
        )
        pg = models.ProductGroup.objects.create(vendor=v1, name="TestPG")
        p = models.Product.objects.create(vendor=v1, product_group=pg, product_id="AAAAAAAAAA")
        expected_result["data"][0]["id"] = p.id
        expected_result["data"][0]["vendor"] = p.vendor.id
        expected_result["data"][0]["product_id"] = p.product_id
        expected_result["data"][0]["product_group"] = pg.id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % expected_result["data"][0]["id"]
        assert Product.objects.count() == 2

        client = APIClient()
        client.login(**AUTH_USER)

        # use product_group field (exact match)
        response = client.get(REST_PRODUCT_LIST + "?product_group__id=%d" % pg.id)
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata["pagination"]["total_records"] == 1, "Expect a single entry in the result"
        assert jdata == expected_result, "unexpected result from API endpoint"


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
class TestProductListAPIEndpoint:
    """Django REST framework API endpoint tests for the Product List model"""
    TEST_PRODUCTS = [
        "Product A",
        "Product B",
        "Product C",
        "Product D",
        "Product E"
    ]
    TEST_PRODUCT_LIST_NAME = "Test Product List"

    def create_test_data(self):
        v = Vendor.objects.get(id=1)
        for e in self.TEST_PRODUCTS:
            models.Product.objects.create(product_id=e, vendor=v)

    def create_test_product_list(self):
        self.create_test_data()
        v = Vendor.objects.get(id=1)
        u = User.objects.get(username="pdb_admin")
        pl = models.ProductList.objects.create(
            name=self.TEST_PRODUCT_LIST_NAME,
            description="<strong>Test Liste</strong>\nJust a test list",
            string_product_list="\n".join(self.TEST_PRODUCTS),
            update_user=u,
            vendor=v
        )

        return pl.id

    def test_token_authentication(self, live_server):
        token, _ = Token.objects.get_or_create(user=User.objects.get(username=AUTH_USER["username"]))

        response = requests.get(live_server + REST_PRODUCTLIST_LIST, headers={
            "Authorization": "Token %s" % token.key
        })

        assert response.status_code == status.HTTP_200_OK, response.text

        response = requests.get(live_server + REST_PRODUCTLIST_LIST, headers={
            "Authorization": "Token invalid_token"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_read_access_with_authenticated_user(self):
        self.create_test_data()
        expected_result = {
            "pagination": {
                "page_records": 1,
                "total_records": 1,
                "url": {
                    "previous": None,
                    "next": None
                },
                "page": 1,
                "last_page": 1
            },
            "data": [
                {
                    "id": 0,
                    "name": "TestList",
                    "vendor": 1,
                    "description": "<strong>Test Liste</strong>\nJust a test list",
                    "string_product_list": self.TEST_PRODUCTS,
                    "update_date": "",
                    "contact_email": "",
                    "url": "http://testserver/productdb/api/v1/productlists/%d/"
                }
            ]
        }
        u = User.objects.get(username="api")
        pl = models.ProductList.objects.create(
            name=expected_result["data"][0]["name"],
            description=expected_result["data"][0]["description"],
            string_product_list="\n".join(expected_result["data"][0]["string_product_list"]),
            update_user=u,
            vendor=Vendor.objects.get(id=1)
        )
        expected_result["data"][0]["id"] = pl.id
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % pl.id
        expected_result["data"][0]["update_date"] = pl.update_date.strftime("%Y-%m-%d")
        expected_result["data"][0]["contact_email"] = u.email

        client = APIClient()
        client.login(**AUTH_USER)

        response = client.get(REST_PRODUCTLIST_LIST)
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not found in result"
        assert jdata["pagination"]["total_records"] == 1, "unexpected result from API endpoint"
        assert jdata == expected_result, "unexpected result from API endpoint"

        # access first element of the list
        response = client.get(jdata["data"][0]["url"])

        assert response.status_code == status.HTTP_200_OK
        assert jdata["data"][0] == response.json()

    def test_add_access_with_permission(self):
        """add action through API for Product List not supported"""
        self.create_test_data()
        test_user = "user"
        test_product_list_id = "Test Product List"

        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="add_productlist")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.add_productlist")

        client = APIClient()
        client.login(username=test_user, password=test_user)

        # create with name
        response = client.post(REST_PRODUCTLIST_LIST, data={"name": test_product_list_id})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert response.json() == {'detail': 'Method "POST" not allowed.'}
        assert ProductList.objects.count() == 0, "no product list was created"

    def test_change_access_with_permission(self):
        id = self.create_test_product_list()

        # create a user with permissions
        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="change_productlist")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.change_productlist")

        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.put(REST_PRODUCTLIST_DETAIL % id, data={"name": "renamed product list"})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, "API endpoint is always read only"
        assert response.json() == {'detail': 'Method "PUT" not allowed.'}

    def test_delete_access_with_permission(self):
        id = self.create_test_product_list()

        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="delete_productlist")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("productdb.delete_productlist")

        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.delete(REST_PRODUCTLIST_DETAIL % id)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED, "API endpoint is always read only"
        assert response.json() == {'detail': 'Method "DELETE" not allowed.'}
        assert ProductList.objects.count() == 1, "no product list was deleted"

    def test_filter_fields(self):
        u = User.objects.create(username="A")
        pl_id = self.create_test_product_list()
        v = Vendor.objects.get(id=1)
        models.ProductList.objects.create(name="Product List", string_product_list="Product A", vendor=v, update_user=u)
        expected_result = {
            "pagination": {
                "page_records": 1,
                "total_records": 1,
                "url": {
                    "previous": None,
                    "next": None
                },
                "page": 1,
                "last_page": 1
            },
            "data": [
                {
                    "id": 0,
                    "name": self.TEST_PRODUCT_LIST_NAME,
                    "description": "<strong>Test Liste</strong>\nJust a test list",
                    "string_product_list": self.TEST_PRODUCTS,
                    "update_date": "",
                    "vendor": v.id,
                    "contact_email": "admin@localhost.localhost",
                    "url": "http://testserver/productdb/api/v1/productlists/%d/"
                }
            ]
        }
        expected_result["data"][0]["id"] = pl_id
        expected_result["data"][0]["update_date"] = date.today().strftime("%Y-%m-%d")
        expected_result["data"][0]["url"] = expected_result["data"][0]["url"] % pl_id

        client = APIClient()
        client.login(**AUTH_USER)

        # use ID field filter (exact match)
        response = client.get(REST_PRODUCTLIST_LIST + "?id=%d" % pl_id)

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata == expected_result, "unexpected result from API endpoint"

        # use name field (contains)
        response = client.get(REST_PRODUCTLIST_LIST + "?name=" + quote(self.TEST_PRODUCT_LIST_NAME.lower()))

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata == expected_result, "unexpected result from API endpoint"

        # use description field (contains)
        response = client.get(REST_PRODUCTLIST_LIST + "?description=" + quote("Just a test"))

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not provided"
        assert jdata == expected_result, "unexpected result from API endpoint"


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
class TestProductIdNormalizationRuleAPIEndpoint:
    """Test Product ID Normalization Rule API Endpoint"""
    def test_token_authentication(self, live_server):
        token, _ = Token.objects.get_or_create(user=User.objects.get(username=AUTH_USER["username"]))

        response = requests.get(live_server + REST_PRODUCTNORMALIZATIONRULE_LIST, headers={
            "Authorization": "Token %s" % token.key
        })

        assert response.status_code == status.HTTP_200_OK, response.text

        response = requests.get(live_server + REST_PRODUCTNORMALIZATIONRULE_LIST, headers={
            "Authorization": "Token invalid_token"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_read_access_with_authenticated_user(self):
        expected_result = {
            "data": [
                {
                    "id": 1,
                    "vendor": None,
                    "product_id": None,
                    "regex_match": None,
                    "comment": None,
                    "priority": None
                }
            ],
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            }
        }
        v = models.Vendor.objects.create(name="vendor")
        pinr = models.ProductIdNormalizationRule.objects.create(vendor=v, regex_match=".*", product_id="PID")
        expected_result["data"][0]["id"] = pinr.id
        expected_result["data"][0]["vendor"] = pinr.vendor_id
        expected_result["data"][0]["product_id"] = pinr.product_id
        expected_result["data"][0]["regex_match"] = pinr.regex_match
        expected_result["data"][0]["comment"] = pinr.comment
        expected_result["data"][0]["priority"] = pinr.priority

        client = APIClient()
        client.login(**AUTH_USER)

        response = client.get(REST_PRODUCTNORMALIZATIONRULE_LIST)
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not found in result"
        assert jdata["pagination"]["total_records"] == 1, "unexpected result from API endpoint"
        assert jdata == expected_result, "unexpected result from API endpoint"

        client = APIClient()
        client.login(**AUTH_USER)

        response = client.get(REST_PRODUCTNORMALIZATIONRULE_DETAIL % pinr.id)

        assert response.status_code == status.HTTP_200_OK
        jdata = response.json()
        assert jdata == expected_result["data"][0], "unexpected result from API endpoint"

    def test_apply_function(self):
        v1 = Vendor.objects.get(id=1)
        pnr = ProductIdNormalizationRule.objects.create(
            vendor=v1,
            product_id="PWR-C1-715WAC=",
            regex_match=r"^PWR\-C1\-715WAC$"
        )
        pnr2 = ProductIdNormalizationRule.objects.create(
            vendor=v1,
            product_id="SOMETHING",
            regex_match=r"^SOMETHIN$"
        )
        pnr3 = ProductIdNormalizationRule.objects.create(
            vendor=v1,
            product_id="PWR-%sWAC=",
            regex_match=r"^PWR\-(\d+)WAC$"
        )

        api_url = REST_PRODUCTNORMALIZATIONRULE_LIST + "apply/"

        client = APIClient()
        client.login(**AUTH_USER)

        response = client.get(api_url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.json().keys()

        response = client.get(api_url + "?input_string=Foo")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.json().keys()

        response = client.get(api_url + "?input_string=Test&vendor_name=None")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.json().keys()

        response = client.get(api_url + "?input_string=Test&vendor_name=Cisco")

        assert response.status_code == status.HTTP_200_OK
        expected_result = {
            "matched_rule_id": None,
            "vendor_id": 1,
            "product_id": "Test",
            "product_in_database": None
        }
        assert response.json() == expected_result
        assert Vendor.objects.get(id=expected_result["vendor_id"]).name == "Cisco Systems"

        response = client.get(api_url + "?input_string=PWR-C1-715WAC&vendor_name=Cisco")

        assert response.status_code == status.HTTP_200_OK
        expected_result = {
            "matched_rule_id": pnr.id,
            "vendor_id": 1,
            "product_id": "PWR-C1-715WAC=",
            "product_in_database": None
        }
        assert response.json() == expected_result
        assert Vendor.objects.get(id=expected_result["vendor_id"]).name == "Cisco Systems"

        p = Product.objects.create(
            product_id="PWR-C1-715WAC=",
            vendor=Vendor.objects.get(id=1)
        )
        pnr.save()
        pnr.refresh_from_db()

        response = client.get(api_url + "?input_string=PWR-C1-715WAC&vendor_name=Cisco")

        assert response.status_code == status.HTTP_200_OK
        expected_result = {
            "matched_rule_id": pnr.id,
            "vendor_id": 1,
            "product_id": "PWR-C1-715WAC=",
            "product_in_database": p.id
        }
        assert response.json() == expected_result
        assert Vendor.objects.get(id=expected_result["vendor_id"]).name == "Cisco Systems"

        # test that the replacement of dynamic values is working
        response = client.get(api_url + "?input_string=PWR-123WAC&vendor_name=Cisco")

        assert response.status_code == status.HTTP_200_OK

        expected_result = {
            "matched_rule_id": pnr3.id,
            "vendor_id": 1,
            "product_id": "PWR-123WAC=",
            "product_in_database": None
        }
        assert response.json() == expected_result


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
class TestNotificationMessageAPIEndpoint:
    """Django REST Framework API endpoint tests for the NotificationMessage model"""
    today_string = DateFormat(datetime.now()).format(get_format(settings.SHORT_DATE_FORMAT))

    def test_token_authentication(self, live_server):
        token, _ = Token.objects.get_or_create(user=User.objects.get(username=AUTH_USER["username"]))

        response = requests.get(live_server + REST_NOTIFICATIONMESSAGES_LIST, headers={
            "Authorization": "Token %s" % token.key
        })

        assert response.status_code == status.HTTP_200_OK, response.text

        response = requests.get(live_server + REST_NOTIFICATIONMESSAGES_LIST, headers={
            "Authorization": "Token invalid_token"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_read_access_with_authenticated_user(self):
        expected_result = {
            "pagination": {
                "page": 1,
                "page_records": 1,
                "url": {
                    "next": None,
                    "previous": None
                },
                "last_page": 1,
                "total_records": 1
            },
            "data": [
                {
                    "id": 1,
                    "title": "FooBar",
                    "type": "INFO",
                    "summary_message": "Test",
                    "detailed_message": "Test",
                    "created": ""
                }
            ]
        }
        nm = NotificationMessage.objects.create(title="A", summary_message="B", detailed_message="C")
        expected_result["data"][0]["id"] = nm.id
        expected_result["data"][0]["title"] = nm.title
        expected_result["data"][0]["summary_message"] = nm.summary_message
        expected_result["data"][0]["detailed_message"] = nm.detailed_message
        expected_result["data"][0]["created"] = nm.created.astimezone(pytz.timezone(settings.TIME_ZONE)).isoformat()

        client = APIClient()
        client.login(**AUTH_USER)

        response = client.get(REST_NOTIFICATIONMESSAGES_LIST)
        assert response.status_code == status.HTTP_200_OK

        jdata = response.json()
        assert "pagination" in jdata, "pagination information not provided"
        assert "data" in jdata, "data branch not found in result"
        assert jdata["pagination"]["total_records"] == 1, "unexpected result from API endpoint"
        assert jdata == expected_result, "unexpected result from API endpoint"

    def test_add_access_with_permission(self):
        test_user = "user"
        expected_result = {
            "id": 1,
            "title": "FooBar",
            "type": "INFO",
            "summary_message": "summary message",
            "detailed_message": "detailed message",
            "created": None
        }

        u = User.objects.create_user(test_user, "", test_user)
        p = Permission.objects.get(codename="add_notificationmessage")
        assert p is not None
        u.user_permissions.add(p)
        u.save()
        assert u.has_perm("config.add_notificationmessage")

        client = APIClient()
        client.login(username=test_user, password=test_user)

        # create with name
        response = client.post(REST_NOTIFICATIONMESSAGES_LIST, data={
            "title": expected_result["title"],
            "summary_message": expected_result["summary_message"],
            "detailed_message": expected_result["detailed_message"]
        })

        assert response.status_code == status.HTTP_201_CREATED, response.content.decode()
        # adjust ID values from Database
        nm_obj = NotificationMessage.objects.get(title=expected_result["title"])
        expected_result["id"] = nm_obj.id
        expected_result["created"] = nm_obj.created.astimezone(pytz.timezone(settings.TIME_ZONE)).isoformat()
        assert response.json() == expected_result, "Should provide the new notification message"

    def test_delete_access_with_permission(self):
        nm = NotificationMessage.objects.create(title="A", summary_message="B", detailed_message="C")
        assert NotificationMessage.objects.count() == 1

        test_user = "user"
        u = User.objects.create_user(test_user, "", test_user)
        perm = Permission.objects.get(codename="delete_notificationmessage")
        assert perm is not None
        u.user_permissions.add(perm)
        u.save()
        assert u.has_perm("config.delete_notificationmessage")

        client = APIClient()
        client.login(username=test_user, password=test_user)
        response = client.delete(REST_NOTIFICATIONMESSAGES_DETAIL % nm.id)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert NotificationMessage.objects.count() == 0
