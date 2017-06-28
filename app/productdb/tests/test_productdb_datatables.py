"""
Test suite for the productdb.datatables module
"""
import pytest
from urllib.parse import quote
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client
from mixer.backend.django import mixer
from rest_framework import status
from app.productdb.models import UserProfile, Vendor

pytestmark = pytest.mark.django_db

AUTH_USER = {
    "username": "api",
    "password": "api"
}


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
def test_datatables_search_on_vendor_products_endpoint():
    test_pid_search_term = "Test Product ID"
    v1 = Vendor.objects.get(name="Cisco Systems")
    for e in range(1, 50):
        mixer.blend("productdb.Product", vendor=v1)
    mixer.blend("productdb.Product", product_id=test_pid_search_term, vendor=v1)
    url = reverse('productdb:datatables_vendor_products_endpoint', kwargs={"vendor_id": v1.id})

    up = UserProfile.objects.get(user=User.objects.get(username=AUTH_USER["username"]))
    assert up.regex_search is False, "Use simple search by default"

    client = Client()
    client.login(**AUTH_USER)

    # call without search term
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 50

    # call with common search term
    response = client.get(url + "?" + quote("search[value]") + "=" + quote(test_pid_search_term))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with case-insensitive common search term
    response = client.get(url + "?" + quote("search[value]") + "=" + quote(test_pid_search_term.lower()))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with column search term
    response = client.get(url + "?" + quote("columns[0][search][value]") + "=" + quote(test_pid_search_term))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with case-insensitive column search term
    response = client.get(url + "?" + quote("columns[0][search][value]") + "=" + quote(test_pid_search_term.lower()))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
def test_datatables_search_on_vendor_products_view():
    test_pid_search_term = "Test Product ID"
    uv = Vendor.objects.get(id=0)
    for e in range(1, 50):
        mixer.blend("productdb.Product", vendor=uv)
    mixer.blend("productdb.Product", product_id=test_pid_search_term, vendor=uv)
    # if the vendor is not specified, the unassigned vendor is used
    url = reverse('productdb:datatables_vendor_products_view')

    up = UserProfile.objects.get(user=User.objects.get(username=AUTH_USER["username"]))
    assert up.regex_search is False, "Use simple search by default"

    client = Client()
    client.login(**AUTH_USER)

    # call without search term
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 50

    # call with common search term
    response = client.get(url + "?" + quote("search[value]") + "=" + quote(test_pid_search_term))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with case-insensitive common search term
    response = client.get(url + "?" + quote("search[value]") + "=" + quote(test_pid_search_term.lower()))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with column search term
    response = client.get(url + "?" + quote("columns[0][search][value]") + "=" + quote(test_pid_search_term))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with case-insensitive column search term
    response = client.get(url + "?" + quote("columns[0][search][value]") + "=" + quote(test_pid_search_term.lower()))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
def test_datatables_search_on_list_products_view():
    test_pid_search_term = "Test Product ID"
    uv = Vendor.objects.get(id=0)
    for e in range(1, 50):
        mixer.blend("productdb.Product", vendor=uv)
    mixer.blend("productdb.Product", product_id=test_pid_search_term, vendor=uv)
    url = reverse('productdb:datatables_list_products_view')

    up = UserProfile.objects.get(user=User.objects.get(username=AUTH_USER["username"]))
    assert up.regex_search is False, "Use simple search by default"

    client = Client()
    client.login(**AUTH_USER)

    # call without search term
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 50

    # call with common search term
    response = client.get(url + "?" + quote("search[value]") + "=" + quote(test_pid_search_term))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with case-insensitive common search term
    response = client.get(url + "?" + quote("search[value]") + "=" + quote(test_pid_search_term.lower()))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with column search term
    response = client.get(url + "?" + quote("columns[1][search][value]") + "=" + quote(test_pid_search_term))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with case-insensitive column search term
    response = client.get(url + "?" + quote("columns[1][search][value]") + "=" + quote(test_pid_search_term.lower()))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
def test_datatables_search_on_list_product_groups_view():
    test_pg_search_term = "Test Product Group"
    uv = Vendor.objects.get(id=0)
    for e in range(1, 50):
        mixer.blend("productdb.ProductGroup", vendor=uv, name="Product Group %d" % e)

    mixer.blend("productdb.ProductGroup", name=test_pg_search_term, vendor=uv)
    url = reverse('productdb:datatables_list_product_groups')

    up = UserProfile.objects.get(user=User.objects.get(username=AUTH_USER["username"]))
    assert up.regex_search is False, "Use simple search by default"

    client = Client()
    client.login(**AUTH_USER)

    # call without search term
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 50

    # call with common search term
    response = client.get(url + "?" + quote("search[value]") + "=" + quote(test_pg_search_term))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with case-insensitive common search term
    response = client.get(url + "?" + quote("search[value]") + "=" + quote(test_pg_search_term.lower()))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with column search term
    response = client.get(url + "?" + quote("columns[1][search][value]") + "=" + quote(test_pg_search_term))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with case-insensitive column search term
    response = client.get(url + "?" + quote("columns[1][search][value]") + "=" + quote(test_pg_search_term.lower()))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
def test_datatables_search_on_list_products_by_product_group_view():
    test_pid_search_term = "Test Product ID"
    uv = Vendor.objects.get(id=0)
    pg = mixer.blend("productdb.ProductGroup")
    for e in range(1, 50):
        mixer.blend("productdb.Product", vendor=uv, product_group=pg)
    mixer.blend("productdb.Product", product_id=test_pid_search_term, vendor=uv, product_group=pg)
    url = reverse('productdb:datatables_list_products_by_group_view', kwargs={"product_group_id": pg.id})

    up = UserProfile.objects.get(user=User.objects.get(username=AUTH_USER["username"]))
    assert up.regex_search is False, "Use simple search by default"

    client = Client()
    client.login(**AUTH_USER)

    # call without search term
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 50

    # call with common search term
    response = client.get(url + "?" + quote("search[value]") + "=" + quote(test_pid_search_term))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with case-insensitive common search term
    response = client.get(url + "?" + quote("search[value]") + "=" + quote(test_pid_search_term.lower()))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with column search term
    response = client.get(url + "?" + quote("columns[0][search][value]") + "=" + quote(test_pid_search_term))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1

    # call with case-insensitive column search term
    response = client.get(url + "?" + quote("columns[0][search][value]") + "=" + quote(test_pid_search_term.lower()))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 1


@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
def test_regex_search_on_list_products_view():
    for e in range(1, 50):
        mixer.blend("productdb.Product", product_id="My Product "
                                                    "ID 0%d" % e)
    mixer.blend("productdb.Product", product_id="My Product ID")
    url = reverse('productdb:datatables_list_products_view')

    up = UserProfile.objects.get(user=User.objects.get(username=AUTH_USER["username"]))
    assert up.regex_search is False, "Use simple search by default"
    # switch to regex based search
    up.regex_search = True
    up.save()

    client = Client()
    client.login(**AUTH_USER)

    # call without search term
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 50

    # call with common search term
    response = client.get(url + "?" + quote("search[value]") + "=" + quote(r"My Product ID \d+"))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 49

    # call with case-insensitive common search term
    response = client.get(url + "?" + quote("search[value]") + "=" + quote(r"My Product ID \d+".lower()))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 49

    # call with column search term
    response = client.get(url + "?" + quote("columns[1][search][value]") + "=" + quote("My Product ID \d+"))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 49

    # call with case-insensitive column search term
    response = client.get(url + "?" + quote("columns[1][search][value]") + "=" + quote("My Product ID \d+".lower()))
    assert response.status_code == status.HTTP_200_OK

    result_json = response.json()
    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json
    assert result_json["recordsFiltered"] == 49


@pytest.mark.usefixtures("import_default_vendors")
def test_vendor_product_list_json_datatables_endpoint():
    for e in range(1, 25):
        mixer.blend("productdb.Vendor")

    url = reverse('productdb:datatables_vendor_products_endpoint', kwargs={'vendor_id': 1})

    client = Client()  # no login required to access the endpoint
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    result_json = response.json()

    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json


@pytest.mark.usefixtures("import_default_vendors")
def test_list_product_groups_json_datatables_endpoint():
    for e in range(1, 25):
        mixer.blend("productdb.ProductGroup")

    url = reverse('productdb:datatables_list_product_groups')

    client = Client()  # no login required to access the endpoint
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    result_json = response.json()

    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json


@pytest.mark.usefixtures("import_default_vendors")
def test_list_products_by_group_json_datatables_endpoint():
    pg = mixer.blend("productdb.ProductGroup")
    for e in range(1, 25):
        mixer.blend("productdb.Product", product_group=pg)

    url = reverse('productdb:datatables_list_products_by_group_view', kwargs={'product_group_id': pg.id})

    client = Client()  # no login required to access the endpoint
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    result_json = response.json()

    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json


@pytest.mark.usefixtures("import_default_vendors")
def test_list_products_json_datatables_endpoint():
    for e in range(1, 25):
        mixer.blend("productdb.Product", list_price=12.34)

    url = reverse('productdb:datatables_list_products_view')

    client = Client()  # no login required to access the endpoint
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    result_json = response.json()

    assert "data" in result_json
    assert "draw" in result_json
    assert "recordsTotal" in result_json
    assert "recordsFiltered" in result_json

    assert result_json["data"][0]["list_price"] == 12.34
