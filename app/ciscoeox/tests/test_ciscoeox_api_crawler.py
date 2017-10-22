"""
Test suite for the ciscoeox.api_crawler module
"""
import pytest
import json
import datetime
import requests
from copy import deepcopy
from mixer.backend.django import mixer
from requests import Response
from app.ciscoeox import api_crawler
from app.ciscoeox.exception import CiscoApiCallFailed, ConnectionFailedException
from app.config.settings import AppSettings
from app.productdb.models import Vendor, Product, ProductMigrationSource, ProductMigrationOption

pytestmark = pytest.mark.django_db
HIT_COUNT = 0


valid_eox_record = {
    "EOLProductID": "WS-C2960-24T-S",
    "LinkToProductBulletinURL": "http://www.cisco.com/en/US/products/hw/switches/ps628/prod_eol_noti"
                                "ce0900aecd804658c9.html",
    "EndOfSvcAttachDate": {
        "value": "2016-10-01",
        "dateFormat": "YYYY-MM-DD"
    },
    "ProductIDDescription": "Some description of the product",
    "EndOfSWMaintenanceReleases": {
        "value": "2016-10-02",
        "dateFormat": "YYYY-MM-DD"
    },
    "EOXInputValue": "WS-C2950* ",
    "UpdatedTimeStamp": {
        "value": "2016-10-03",
        "dateFormat": "YYYY-MM-DD"
    },
    "EndOfServiceContractRenewal": {
        "value": "2016-10-04",
        "dateFormat": "YYYY-MM-DD"
    },
    "EOXInputType": "ShowEOXByPids",
    "EndOfSaleDate": {
        "value": "2016-10-05",
        "dateFormat": "YYYY-MM-DD"
    },
    "EndOfRoutineFailureAnalysisDate": {
        "value": "2016-10-06",
        "dateFormat": "YYYY-MM-DD"
    },
    "EOXMigrationDetails": {
        "MigrationProductInfoURL": " ",
        "MigrationInformation": "^Catalyst 2960 24 10/100/1000, 4 T/SFP LAN Base Image",
        "MigrationProductName": " ",
        "MigrationOption": "Enter PID(s)",
        "MigrationStrategy": " ",
        "PIDActiveFlag": "Y  ",
        "MigrationProductId": "WS-C2960G-24TC-L"
    },
    "EOXExternalAnnouncementDate": {
        "value": "2016-10-07",
        "dateFormat": "YYYY-MM-DD"
    },
    "LastDateOfSupport": {
        "value": "2016-10-08",
        "dateFormat": "YYYY-MM-DD"
    },
    "ProductBulletinNumber": "12345"
}


@pytest.fixture
def enable_cisco_api():
    app = AppSettings()
    app.set_cisco_api_enabled(True)


@pytest.fixture
def enabled_autocreate_new_products():
    app = AppSettings()
    app.set_auto_create_new_products(True)


@pytest.fixture
def disable_cisco_api():
    app = AppSettings()
    app.set_cisco_api_enabled(False)


def test_convert_time_format():
    """test the translation function for the time format (from Cisco API to python)"""
    assert api_crawler.convert_time_format("YYYY-MM-DD") == "%Y-%m-%d"
    assert api_crawler.convert_time_format("DD-MM-YYYY") == "%Y-%m-%d"


@pytest.mark.usefixtures("load_test_cisco_api_credentials")
@pytest.mark.usefixtures("import_default_vendors")
class TestGetRawApiData:
    @pytest.mark.usefixtures("enable_cisco_api")
    def test_invalid_cisco_eox_database_query(self):
        with pytest.raises(ValueError) as exinfo:
            api_crawler.get_raw_api_data(None)

        assert exinfo.match("api_query must be a string value")

    @pytest.mark.usefixtures("mock_cisco_api_authentication_server")
    @pytest.mark.usefixtures("enable_cisco_api")
    def test_cisco_eox_database_query_with_server_error(self, monkeypatch):
        class MockSession:
            def get(self, *args, **kwargs):
                raise Exception("Server is down")
        monkeypatch.setattr(requests, "Session", MockSession)

        with pytest.raises(ConnectionFailedException) as exinfo:
            api_crawler.get_raw_api_data("MyQuery")

        assert exinfo.match("cannot contact API endpoint at")

    @pytest.mark.usefixtures("disable_cisco_api")
    def test_cisco_eox_database_query_with_disabled_cisco_eox_api(self):
        with pytest.raises(CiscoApiCallFailed) as exinfo:
            api_crawler.get_raw_api_data("MyQuery")

        assert exinfo.match("Cisco API access not enabled")

    @pytest.mark.usefixtures("mock_cisco_api_authentication_server")
    @pytest.mark.usefixtures("enable_cisco_api")
    def test_offline_invalid_update_cisco_eox_database_with_default_settings(self, monkeypatch):
        # mock the underlying GET request
        class MockSession:
            def get(self, *args, **kwargs):
                r = Response()
                r.status_code = 200
                with open("app/ciscoeox/tests/data/cisco_eox_error_response.json") as f:
                    r._content = f.read().encode("utf-8")
                return r
        monkeypatch.setattr(requests, "Session", MockSession)

        with pytest.raises(CiscoApiCallFailed) as exinfo:
            api_crawler.get_raw_api_data("WS-C2950G-48-EI-WS")

    @pytest.mark.usefixtures("mock_cisco_api_authentication_server")
    @pytest.mark.usefixtures("enable_cisco_api")
    def test_single_page_results(self, monkeypatch):
        # mock the underlying GET request
        class MockSession:
            def get(self, *args, **kwargs):
                r = Response()
                r.status_code = 200
                with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_1.json") as f:
                    r._content = f.read().encode("utf-8")
                return r
        monkeypatch.setattr(requests, "Session", MockSession)

        result = api_crawler.get_raw_api_data("WS-C2950G-48-EI-WS")

        assert len(result) == 3, "Three products should be imported"
        # every product should contain the following values
        for e in result:
            assert "EOLProductID" in e.keys()
            assert "EOXMigrationDetails" in e.keys()
            assert "ProductIDDescription" in e.keys()

    @pytest.mark.usefixtures("mock_cisco_api_authentication_server")
    @pytest.mark.usefixtures("enabled_autocreate_new_products")
    @pytest.mark.usefixtures("enable_cisco_api")
    def test_multi_page_results(self, monkeypatch):
        # mock the underlying GET request
        class MockSession:
            def get(self, *args, **kwargs):
                global HIT_COUNT
                HIT_COUNT += 1
                r = Response()
                r.status_code = 200
                if HIT_COUNT == 1:
                    with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_2.json") as f:
                        r._content = f.read().encode("utf-8")

                else:
                    with open("app/ciscoeox/tests/data/cisco_eox_response_page_2_of_2.json") as f:
                        r._content = f.read().encode("utf-8")
                return r
        monkeypatch.setattr(requests, "Session", MockSession)

        result = api_crawler.get_raw_api_data("WS-C2950G-48-EI-WS")

        assert len(result) == 3, "Three products should be imported"
        # every product should contain the following values
        for e in result:
            assert "EOLProductID" in e.keys()
            assert "EOXMigrationDetails" in e.keys()
            assert "ProductIDDescription" in e.keys()


@pytest.mark.usefixtures("import_default_vendors")
class TestUpdateLocalDbBasedOnRecord:
    def test_with_valid_new_records(self):
        result = api_crawler.update_local_db_based_on_record(valid_eox_record)

        assert result is None
        assert Product.objects.count() == 0, "No product was created, because the created flag was not set"

    def test_with_valid_new_records_and_create_missing(self):
        result = api_crawler.update_local_db_based_on_record(valid_eox_record, create_missing=True)

        assert result is None
        assert Product.objects.count() == 1, "Product is not created"

        p = Product.objects.get(product_id="WS-C2960-24T-S")

        assert p.end_of_new_service_attachment_date == datetime.date(2016, 10, 1)
        assert p.end_of_sw_maintenance_date == datetime.date(2016, 10, 2)
        assert p.eox_update_time_stamp == datetime.date(2016, 10, 3)
        assert p.end_of_service_contract_renewal == datetime.date(2016, 10, 4)
        assert p.end_of_sale_date == datetime.date(2016, 10, 5)
        assert p.end_of_routine_failure_analysis == datetime.date(2016, 10, 6)
        assert p.eol_ext_announcement_date == datetime.date(2016, 10, 7)
        assert p.end_of_support_date == datetime.date(2016, 10, 8)
        assert p.eol_reference_number == "12345"
        assert p.eol_reference_url == "http://www.cisco.com/en/US/products/hw/switches/ps628/prod_eol_notice0" \
                                      "900aecd804658c9.html"

    @pytest.mark.usefixtures("import_default_vendors")
    def test_update_local_db_based_on_record(self):
        mixer.blend("productdb.ProductGroup", name="Catalyst 2960")
        assert Product.objects.count() == 0

        # test call with invalid data
        with pytest.raises(KeyError):
            api_crawler.update_local_db_based_on_record({})

        # test call with valid data and create flag
        result = api_crawler.update_local_db_based_on_record(valid_eox_record, create_missing=True)

        assert result is None
        assert Product.objects.count() == 1, "The product should be created"

        # test call with valid data that already exist in the database
        result = api_crawler.update_local_db_based_on_record(valid_eox_record, create_missing=True)

        assert result is None
        assert Product.objects.count() == 1, "The product should be created"

        p = Product.objects.get(product_id="WS-C2960-24T-S")
        assert p.description == "Some description of the product"
        assert p.end_of_new_service_attachment_date == datetime.date(2016, 10, 1)
        assert p.end_of_sw_maintenance_date == datetime.date(2016, 10, 2)
        assert p.eox_update_time_stamp == datetime.date(2016, 10, 3)
        assert p.end_of_service_contract_renewal == datetime.date(2016, 10, 4)
        assert p.end_of_sale_date == datetime.date(2016, 10, 5)
        assert p.end_of_routine_failure_analysis == datetime.date(2016, 10, 6)
        assert p.eol_ext_announcement_date == datetime.date(2016, 10, 7)
        assert p.end_of_support_date == datetime.date(2016, 10, 8)
        assert p.eol_reference_number == "12345"
        assert p.eol_reference_url == "http://www.cisco.com/en/US/products/hw/switches/ps628/prod_eol_notice0" \
                                      "900aecd804658c9.html"

        # test call with valid data (updated)
        p = Product.objects.get(product_id="WS-C2960-24T-S")
        p.eox_update_time_stamp = datetime.datetime(1999, 1, 1)
        p.save()

        result = api_crawler.update_local_db_based_on_record(valid_eox_record, create_missing=True)

        assert result is None
        assert Product.objects.count() == 1, "The product was only updated"

        p = Product.objects.get(product_id="WS-C2960-24T-S")
        assert p.end_of_service_contract_renewal == datetime.date(2016, 10, 4), "Should be the value prior the update"

        # test crash of the update method during update
        p = Product.objects.get(product_id="WS-C2960-24T-S")
        p.eox_update_time_stamp = datetime.datetime(1999, 1, 1)  # reset the eox timestamp to trigger the update
        p.save()

        invalid_record = deepcopy(valid_eox_record)
        invalid_record["EndOfSWMaintenanceReleases"]["value"] = None
        invalid_record["EndOfServiceContractRenewal"]["value"] = "2016-10-30"  # value in db at this time: "2016-10-04"

        result = api_crawler.update_local_db_based_on_record(invalid_record, create_missing=True)

        assert result == "Product Data update failed: strptime() argument 1 must be str, not None"
        assert Product.objects.count() == 1, "The transaction should rollback to avoid inconsistent entries in the DB"

        # verify that the change were not saved
        p = Product.objects.get(product_id="WS-C2960-24T-S")
        assert p.eox_update_time_stamp == datetime.date(1999, 1, 1), "Should be the value prior the update"
        assert p.end_of_service_contract_renewal == datetime.date(2016, 10, 4), "Should be the value prior the update"

        # test crash of the update method during create
        invalid_record = deepcopy(valid_eox_record)
        invalid_record["EOLProductID"] = "MyTest123"
        invalid_record["EndOfRoutineFailureAnalysisDate"]["value"] = None

        result = api_crawler.update_local_db_based_on_record(invalid_record, create_missing=True)

        assert result == "Product Data update failed: strptime() argument 1 must be str, not None"
        assert Product.objects.count() == 1, "The transaction should rollback to avoid inconsistent entries in the DB"

        p = Product.objects.get(product_id="WS-C2960-24T-S")
        assert p.end_of_service_contract_renewal == datetime.date(2016, 10, 4), "Should be the value prior the update"

        # test record with invalid URL
        invalid_record = deepcopy(valid_eox_record)
        invalid_record["LinkToProductBulletinURL"] = "Not yet provided"
        invalid_record["EOLProductID"] = "xyz"

        result = api_crawler.update_local_db_based_on_record(invalid_record, create_missing=True)

        assert result == "Product Data update failed: invalid EoL reference URL"
        assert Product.objects.count() == 1, "The transaction should rollback to avoid inconsistent entries in the DB"

        p = Product.objects.get(product_id="WS-C2960-24T-S")
        assert p.end_of_service_contract_renewal == datetime.date(2016, 10, 4), "Should be the value prior the update"

    def test_migration_options_from_update_local_db_based_on_eox_record(self):
        mixer.blend("productdb.ProductGroup", name="Catalyst 2960")
        assert Product.objects.count() == 0
        assert ProductMigrationSource.objects.filter(name="Cisco EoX Migration option").count() == 0

        # load eox_response with test migration data
        with open("app/ciscoeox/tests/data/cisco_eox_reponse_migration_data.json") as f:
            eox_records = json.loads(f.read())

        # test with valid migration option
        result = api_crawler.update_local_db_based_on_record(eox_records["EOXRecord"][0], create_missing=True)
        assert result is None
        assert ProductMigrationSource.objects.filter(name="Cisco EoX Migration option").count() == 1

        p = Product.objects.get(product_id="WS-C2950T-48-SI-WS", vendor=Vendor.objects.get(id=1))

        assert p.has_migration_options() is True
        assert p.get_product_migration_source_names_set() == ["Cisco EoX Migration option"]

        pmo = p.get_preferred_replacement_option()
        assert type(pmo) == ProductMigrationOption
        assert pmo.replacement_product_id == "WS-C2960G-48TC-L"
        assert pmo.comment == ""
        assert pmo.migration_product_info_url == ""
        assert pmo.is_replacement_in_db() is False
        assert pmo.is_valid_replacement() is True
        assert pmo.get_valid_replacement_product() is None

        # create product in database (state of the PMO should change)
        rep = mixer.blend("productdb.Product", product_id="WS-C2960G-48TC-L", vendor=Vendor.objects.get(id=1))
        pmo.refresh_from_db()
        assert pmo.is_replacement_in_db() is True
        assert pmo.get_valid_replacement_product().product_id == rep.product_id

        # test with missing replacement product
        result = api_crawler.update_local_db_based_on_record(eox_records["EOXRecord"][1], create_missing=True)
        assert result is None
        assert ProductMigrationSource.objects.filter(name="Cisco EoX Migration option").count() == 1

        p = Product.objects.get(product_id="WS-C2950G-24-EI", vendor=Vendor.objects.get(id=1))

        assert p.has_migration_options() is True
        assert p.get_product_migration_source_names_set() == ["Cisco EoX Migration option"]

        pmo = p.get_preferred_replacement_option()
        assert type(pmo) == ProductMigrationOption
        assert pmo.replacement_product_id == ""
        assert pmo.comment == "No Replacement Available"
        assert pmo.migration_product_info_url == "http://www.cisco.com/en/US/products/ps10538/index.html"
        assert pmo.is_replacement_in_db() is False
        assert pmo.is_valid_replacement() is False
        assert pmo.get_valid_replacement_product() is None

        # test with custom migration (no direct link to a product)
        result = api_crawler.update_local_db_based_on_record(eox_records["EOXRecord"][2], create_missing=True)
        assert result is None
        assert ProductMigrationSource.objects.filter(name="Cisco EoX Migration option").count() == 1

        p = Product.objects.get(product_id="WS-C2950G-48-EI-WS", vendor=Vendor.objects.get(id=1))

        assert p.has_migration_options() is True
        assert p.get_product_migration_source_names_set() == ["Cisco EoX Migration option"]

        pmo = p.get_preferred_replacement_option()
        assert type(pmo) == ProductMigrationOption
        assert pmo.replacement_product_id == ""
        assert pmo.comment == "Customers are encouraged to migrate to the Cisco 8540 Wireless Controller. Information " \
                              "about this product can be found at http://www.cisco.com/c/en/us/products/wireless/8540-" \
                              "wireless-controller/index.html."
        assert pmo.migration_product_info_url == "http://www.cisco.com/c/en/us/products/wireless/8540-wireless-" \
                                                 "controller/index.html"
        assert pmo.is_replacement_in_db() is False
        assert pmo.is_valid_replacement() is False
        assert pmo.get_valid_replacement_product() is None


def test_clean_url_values():
    """
    test case to clean the URL values from the Cisco API response
    :return:
    """
    test_sets = {
        # input, expected
        "": "",
        " ": "",
        "http://localhost ": "http://localhost",
        "http://localhost": "http://localhost",
        "https://localhost": "https://localhost",
        "https://localhost;http://another_localhost": "https://localhost",
        "https://localhost and http://another_localhost": "https://localhost",
        "https://localhost and https://another_localhost": "https://localhost",
        "https://localhost; and http://another_localhost": "https://localhost",
        "https://localhost; and https://another_localhost": "https://localhost",
        "https://localhost http://another_localhost": "https://localhost",
        "https://localhost https://another_localhost": "https://localhost",
        "https://localhost or http://another_localhost": "https://localhost",
        "https://localhost or https://another_localhost": "https://localhost",
        "https://localhost; or http://another_localhost": "https://localhost",
        "https://localhost; or https://another_localhost": "https://localhost",
    }

    for input, exp_output in test_sets.items():
        output = api_crawler.clean_api_url_response(input)
        assert output == exp_output
