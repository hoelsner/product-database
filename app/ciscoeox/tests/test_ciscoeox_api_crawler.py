"""
Test suite for the ciscoeox.api_crawler module
"""
import pytest
import json
import datetime
import requests
from mixer.backend.django import mixer
from requests import Response
from app.ciscoeox import api_crawler
from app.ciscoeox.exception import CiscoApiCallFailed, ConnectionFailedException
from app.productdb.models import Vendor, Product

pytestmark = pytest.mark.django_db
CISCO_API_ENABLED = True
PRODUCT_BLACKLIST_REGEX = ""
AUTO_CREATE_NEW_PRODUCTS = False
HIT_COUNT = 0


class BaseCiscoApiConsoleSettings:
    """
    Mock object that provides the Cisco API credentials used for online tests. If no credentials are found, dummy
    values are used. The source file for the Test API credentials are read from the ".cisco_api_credentials" file,
    which should have the following format:

    {
        "id": "",
        "secret": ""
    }

    """
    CREDENTIALS_FILE = ".cisco_api_credentials"

    def read_file(self):
        pass

    def load_client_credentials(self):
        pass

    def is_cisco_api_enabled(self):
        return CISCO_API_ENABLED

    def get_product_blacklist_regex(self):
        return PRODUCT_BLACKLIST_REGEX

    def is_auto_create_new_products(self):
        return AUTO_CREATE_NEW_PRODUCTS

    def get_cisco_api_client_id(self):
        try:
            with open(self.CREDENTIALS_FILE) as f:
                return json.loads(f.read())["client_id"]
        except:
            return "dummy_id"

    def get_cisco_api_client_secret(self):
        try:
            with open(self.CREDENTIALS_FILE) as f:
                return json.loads(f.read())["client_secret"]
        except:
            return "dummy_secret"


@pytest.fixture
def use_test_api_configuration(monkeypatch):
    monkeypatch.setattr(api_crawler, "AppSettings", BaseCiscoApiConsoleSettings)


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


def test_convert_time_format():
    """test the translation function for the time format (from Cisco API to python)"""
    assert api_crawler.convert_time_format("YYYY-MM-DD") == "%Y-%m-%d"
    assert api_crawler.convert_time_format("DD-MM-YYYY") == "%Y-%m-%d"


@pytest.mark.usefixtures("import_default_vendors")
def test_product_id_in_database(monkeypatch):
    """test the helper function, that a given Product ID exists in the database"""
    assert api_crawler.product_id_in_database(None) is False

    test_query = "WS-C2960-24T-S"
    assert api_crawler.product_id_in_database(test_query) is False

    mixer.blend("productdb.Product", product_id=test_query, vendor=Vendor.objects.get(id=1))
    assert api_crawler.product_id_in_database(test_query) is True

    def unexpected_exception():
        raise Exception
    monkeypatch.setattr(Product.objects, "filter", lambda: unexpected_exception)

    assert api_crawler.product_id_in_database(test_query) is False


@pytest.mark.usefixtures("import_default_vendors")
def test_update_local_db_based_on_record():
    mixer.blend("productdb.ProductGroup", name="Catalyst 2960")
    assert Product.objects.count() == 0

    # test call with invalid data
    with pytest.raises(KeyError):
        api_crawler.update_local_db_based_on_record({})

    # test call with valid data
    result = api_crawler.update_local_db_based_on_record(valid_eox_record)

    assert "PID" in result
    assert result["PID"] == "WS-C2960-24T-S"
    assert "blacklist" in result
    assert result["blacklist"] is False
    assert "created" in result
    assert result["created"] is False
    assert "updated" in result
    assert result["updated"] is False
    assert "message" in result
    assert result["message"] is None
    assert Product.objects.count() == 0, "No product was created, because the created flag was not set"

    # test call with valid data and create flag
    result = api_crawler.update_local_db_based_on_record(valid_eox_record, create_missing=True)

    assert "PID" in result
    assert result["PID"] == "WS-C2960-24T-S"
    assert "blacklist" in result
    assert result["blacklist"] is False
    assert "created" in result
    assert result["created"] is True
    assert "updated" in result
    assert result["updated"] is True
    assert "message" in result
    assert result["message"] is None
    assert Product.objects.count() == 1, "The product should be created"

    # test call with valid data that already exist in the database
    result = api_crawler.update_local_db_based_on_record(valid_eox_record, create_missing=True)

    assert "PID" in result
    assert result["PID"] == "WS-C2960-24T-S"
    assert "blacklist" in result
    assert result["blacklist"] is False
    assert "created" in result
    assert result["created"] is False
    assert "updated" in result
    assert result["updated"] is False
    assert "message" in result
    assert "update suppressed" in result["message"]
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

    assert "PID" in result
    assert result["PID"] == "WS-C2960-24T-S"
    assert "blacklist" in result
    assert result["blacklist"] is False
    assert "created" in result
    assert result["created"] is False
    assert "updated" in result
    assert result["updated"] is True
    assert "message" in result
    assert result["message"] is None
    assert Product.objects.count() == 1, "The product was only updated"

    p = Product.objects.get(product_id="WS-C2960-24T-S")
    assert p.end_of_service_contract_renewal == datetime.date(2016, 10, 4), "Should be the value prior the update"

    # test crash of the update method during update
    p = Product.objects.get(product_id="WS-C2960-24T-S")
    p.eox_update_time_stamp = datetime.datetime(1999, 1, 1)  # reset the eox timestamp to trigger the update
    p.save()

    invalid_record = valid_eox_record.copy()
    invalid_record["EndOfSWMaintenanceReleases"]["value"] = None
    invalid_record["EndOfServiceContractRenewal"]["value"] = "2016-10-30"  # value in db at this time: "2016-10-04"

    result = api_crawler.update_local_db_based_on_record(invalid_record, create_missing=True)

    assert "PID" in result
    assert result["PID"] == "WS-C2960-24T-S"
    assert "blacklist" in result
    assert result["blacklist"] is False
    assert "created" in result
    assert result["created"] is False
    assert "updated" in result
    assert result["updated"] is True
    assert "message" in result
    assert "Update failed: " in result["message"]
    assert Product.objects.count() == 1, "The transaction should rollback to avoid inconsistent entries in the DB"

    # verify that the change were not saved
    p = Product.objects.get(product_id="WS-C2960-24T-S")
    assert p.eox_update_time_stamp == datetime.date(1999, 1, 1), "Should be the value prior the update"
    assert p.end_of_service_contract_renewal == datetime.date(2016, 10, 4), "Should be the value prior the update"

    # test crash of the update method during create
    invalid_record = valid_eox_record.copy()
    invalid_record["EOLProductID"] = "MyTest123"
    invalid_record["EndOfRoutineFailureAnalysisDate"]["value"] = None

    result = api_crawler.update_local_db_based_on_record(invalid_record, create_missing=True)

    assert "PID" in result
    assert result["PID"] == "MyTest123"
    assert "blacklist" in result
    assert result["blacklist"] is False
    assert "created" in result
    assert result["created"] is True
    assert "updated" in result
    assert result["updated"] is True
    assert "message" in result
    assert "Update failed: " in result["message"]
    assert Product.objects.count() == 1, "The transaction should rollback to avoid inconsistent entries in the DB"

    p = Product.objects.get(product_id="WS-C2960-24T-S")
    assert p.end_of_service_contract_renewal == datetime.date(2016, 10, 4), "Should be the value prior the update"

    # test record with invalid URL
    invalid_record = valid_eox_record.copy()
    invalid_record["LinkToProductBulletinURL"] = "Not yet provided"
    invalid_record["EOLProductID"] = "xyz"

    result = api_crawler.update_local_db_based_on_record(invalid_record, create_missing=True)

    assert "PID" in result
    assert result["PID"] == "xyz"
    assert "blacklist" in result
    assert result["blacklist"] is False
    assert "created" in result
    assert result["created"] is True
    assert "updated" in result
    assert result["updated"] is True
    assert "message" in result
    assert "Update failed: " in result["message"]
    assert Product.objects.count() == 1, "The transaction should rollback to avoid inconsistent entries in the DB"

    p = Product.objects.get(product_id="WS-C2960-24T-S")
    assert p.end_of_service_contract_renewal == datetime.date(2016, 10, 4), "Should be the value prior the update"


@pytest.mark.usefixtures("use_test_api_configuration")
@pytest.mark.usefixtures("import_default_vendors")
class TestUpdateCiscoEoxDatabase:
    def test_invalid_cisco_eox_database_query(self):
        with pytest.raises(ValueError) as exinfo:
            api_crawler.update_cisco_eox_database(None)

        assert exinfo.match("api_query must be a string value")

    def test_cisco_eox_database_query_with_server_error(self, monkeypatch):
        def raise_error():
            raise Exception("Server is down")

        monkeypatch.setattr(requests, "get", raise_error)

        with pytest.raises(ConnectionFailedException) as exinfo:
            api_crawler.update_cisco_eox_database("MyQuery")

        assert exinfo.match("cannot contact API endpoint at")

    def test_cisco_eox_database_query_with_disabled_cisco_eox_api(self):
        global CISCO_API_ENABLED
        CISCO_API_ENABLED = False

        with pytest.raises(CiscoApiCallFailed) as exinfo:
            api_crawler.update_cisco_eox_database("MyQuery")

        assert exinfo.match("Cisco API access not enabled")

        CISCO_API_ENABLED = True

    def test_offline_invalid_update_cisco_eox_database_with_default_settings(self, monkeypatch):
        # mock the underlying GET request
        def mock_response():
            r = Response()
            r.status_code = 200
            with open("app/ciscoeox/tests/data/cisco_eox_error_response.json") as f:
                r._content = f.read().encode("utf-8")
            return r

        monkeypatch.setattr(requests, "get", lambda x, headers: mock_response())

        with pytest.raises(CiscoApiCallFailed) as exinfo:
            api_crawler.update_cisco_eox_database("WS-C2950G-48-EI-WS")

        assert exinfo.match("Cisco EoX API error: Some unknown error occurred during the API access \(YXCABC\)")

    def test_offline_valid_update_cisco_eox_database_with_default_settings(self, monkeypatch):
        # mock the underlying GET request
        def mock_response():
            r = Response()
            r.status_code = 200
            with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_1.json") as f:
                r._content = f.read().encode("utf-8")
            return r

        monkeypatch.setattr(requests, "get", lambda x, headers: mock_response())

        result = api_crawler.update_cisco_eox_database("WS-C2950G-48-EI-WS")

        assert len(result) == 3, "Three products should be imported"
        # every product should contain the following values
        for e in result:
            assert "blacklist" in e
            assert "updated" in e
            assert "created" in e
            assert "PID" in e
            assert "message" in e

            assert e["blacklist"] is False
            assert e["updated"] is False
            assert e["created"] is False
            assert type(e["PID"]) == str
            assert e["message"] is None

        assert Product.objects.count() == 0, "No products are created, because the creation mode is disabled by default"

    def test_offline_valid_update_cisco_eox_database_with_multiple_urls_in_result(self, monkeypatch):
        # mock the underlying GET request
        def mock_response():
            r = Response()
            r.status_code = 200
            with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_1.json") as f:
                raw_data = f.read()
            jdata = json.loads(raw_data)

            jdata["EOXRecord"][0]["EOLProductID"] = "TEST_PID"
            jdata["EOXRecord"][0]["LinkToProductBulletinURL"] = "http://somewhere.com/index.html ," \
                                                                "https://other.com/index.html"
            r._content = json.dumps(jdata).encode("utf-8")
            return r

        monkeypatch.setattr(requests, "get", lambda x, headers: mock_response())

        global AUTO_CREATE_NEW_PRODUCTS
        AUTO_CREATE_NEW_PRODUCTS = True
        result = api_crawler.update_cisco_eox_database("WS-C2950G-48-EI-WS")

        assert len(result) == 3, "Three products should be seen in the API response"
        assert Product.objects.count() == 3, "Three products should be imported to the database"

        p = Product.objects.get(product_id="TEST_PID")
        assert p.eol_reference_url == "http://somewhere.com/index.html", "only the first entry is stored in the " \
                                                                         "database"

    def test_offline_no_result_update_cisco_eox_database_with_create_flag(self, monkeypatch):
        # mock the underlying GET request
        def mock_response():
            r = Response()
            r.status_code = 200
            with open("app/ciscoeox/tests/data/cisco_eox_no_result_response.json") as f:
                r._content = f.read().encode("utf-8")
            return r

        monkeypatch.setattr(requests, "get", lambda x, headers: mock_response())

        global AUTO_CREATE_NEW_PRODUCTS
        AUTO_CREATE_NEW_PRODUCTS = True
        result = api_crawler.update_cisco_eox_database("WS-C2950G-48-EI-WS")

        assert len(result) == 1, "Three products should be imported"
        assert "blacklist" in result[0]
        assert "updated" in result[0]
        assert "created" in result[0]
        assert "PID" in result[0]
        assert "message" in result[0]

        assert result[0]["blacklist"] is False
        assert result[0]["updated"] is False
        assert result[0]["created"] is False
        assert result[0]["PID"] is None
        assert result[0]["message"] == "No product update required"

        assert Product.objects.count() == 0, "No products are created, because the creation mode is disabled by default"

        AUTO_CREATE_NEW_PRODUCTS = False

    def test_offline_valid_update_cisco_eox_database_with_create_flag(self, monkeypatch):
        # mock the underlying GET request
        def mock_response():
            r = Response()
            r.status_code = 200
            with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_1.json") as f:
                r._content = f.read().encode("utf-8")
            return r

        monkeypatch.setattr(requests, "get", lambda x, headers: mock_response())

        global AUTO_CREATE_NEW_PRODUCTS
        AUTO_CREATE_NEW_PRODUCTS = True
        result = api_crawler.update_cisco_eox_database("WS-C2950G-48-EI-WS")

        assert len(result) == 3, "Three products should be imported"
        # every product should contain the following values
        for e in result:
            assert "blacklist" in e
            assert "updated" in e
            assert "created" in e
            assert "PID" in e
            assert "message" in e

            assert e["blacklist"] is False
            assert e["updated"] is True
            assert e["created"] is True
            assert type(e["PID"]) == str
            assert e["message"] is None

        assert Product.objects.count() == 3, "Products from the test API results are created"

        # call the same query again
        result = api_crawler.update_cisco_eox_database("WS-C2950G-48-EI-WS")

        for e in result:
            assert "blacklist" in e
            assert "updated" in e
            assert "created" in e
            assert "PID" in e
            assert "message" in e

            assert e["blacklist"] is False
            assert e["updated"] is False
            assert e["created"] is False
            assert type(e["PID"]) == str
            assert e["message"] == "update suppressed (data not modified)"

        assert len(result) == 3, "Nothing should change"

        AUTO_CREATE_NEW_PRODUCTS = False

    def test_offline_valid_update_cisco_eox_database_with_create_flag_and_multipage_result(self, monkeypatch):
        # mock the underlying GET request
        def mock_response():
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

        monkeypatch.setattr(requests, "get", lambda x, headers: mock_response())

        global AUTO_CREATE_NEW_PRODUCTS
        AUTO_CREATE_NEW_PRODUCTS = True
        result = api_crawler.update_cisco_eox_database("WS-C2950G-48-EI-WS")

        assert len(result) == 3, "Three products should be imported"
        # every product should contain the following values
        for e in result:
            assert "blacklist" in e
            assert "updated" in e
            assert "created" in e
            assert "PID" in e
            assert "message" in e

            assert e["blacklist"] is False
            assert e["updated"] is True
            assert e["created"] is True
            assert type(e["PID"]) == str
            assert e["message"] is None

        assert Product.objects.count() == 3, "No products are created, because the creation mode is disabled by default"
        AUTO_CREATE_NEW_PRODUCTS = False

    def test_offline_valid_update_cisco_eox_database_with_create_flag_and_blacklist(self, monkeypatch):
        # mock the underlying GET request
        def mock_response():
            r = Response()
            r.status_code = 200
            with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_1.json") as f:
                r._content = f.read().encode("utf-8")
            return r

        monkeypatch.setattr(requests, "get", lambda x, headers: mock_response())

        global AUTO_CREATE_NEW_PRODUCTS
        global PRODUCT_BLACKLIST_REGEX
        AUTO_CREATE_NEW_PRODUCTS = True
        PRODUCT_BLACKLIST_REGEX = "WS-C2950G-48-EI-WS"
        result = api_crawler.update_cisco_eox_database("WS-C2950G-48-EI-WS")

        assert len(result) == 3, "Three products should be imported"
        # every product should contain the following values
        for e in result:
            assert "blacklist" in e
            assert "updated" in e
            assert "created" in e
            assert "PID" in e
            assert "message" in e

            if e["PID"] == "WS-C2950G-48-EI-WS":
                assert e["blacklist"] is True
                assert e["updated"] is False
                assert e["created"] is False
                assert type(e["PID"]) == str
                assert e["message"] is None
            else:
                assert e["blacklist"] is False
                assert e["updated"] is True
                assert e["created"] is True
                assert type(e["PID"]) == str
                assert e["message"] is None

        assert Product.objects.count() == 2, "No products are created, because the creation mode is disabled by default"
        AUTO_CREATE_NEW_PRODUCTS = False
        PRODUCT_BLACKLIST_REGEX = ""

    def test_offline_valid_update_cisco_eox_database_with_create_flag_and_regex_blacklist(self, monkeypatch):
        # mock the underlying GET request
        def mock_response():
            r = Response()
            r.status_code = 200
            with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_1.json") as f:
                r._content = f.read().encode("utf-8")
            return r

        monkeypatch.setattr(requests, "get", lambda x, headers: mock_response())

        global AUTO_CREATE_NEW_PRODUCTS
        global PRODUCT_BLACKLIST_REGEX
        AUTO_CREATE_NEW_PRODUCTS = True
        PRODUCT_BLACKLIST_REGEX = ".*-C2950G-48-EI-WS$"
        result = api_crawler.update_cisco_eox_database("WS-C2950G-48-EI-WS")

        assert len(result) == 3, "Three products should be imported"
        # every product should contain the following values
        for e in result:
            assert "blacklist" in e
            assert "updated" in e
            assert "created" in e
            assert "PID" in e
            assert "message" in e

            if e["PID"] == "WS-C2950G-48-EI-WS":
                assert e["blacklist"] is True
                assert e["updated"] is False
                assert e["created"] is False
                assert type(e["PID"]) == str
                assert e["message"] is None
            else:
                assert e["blacklist"] is False
                assert e["updated"] is True
                assert e["created"] is True
                assert type(e["PID"]) == str
                assert e["message"] is None

        assert Product.objects.count() == 2, "No products are created, because the creation mode is disabled by default"
        AUTO_CREATE_NEW_PRODUCTS = False
        PRODUCT_BLACKLIST_REGEX = ""

    def test_offline_valid_update_cisco_eox_database_with_create_flag_and_invalid_blacklist(self, monkeypatch):
        # mock the underlying GET request
        def mock_response():
            r = Response()
            r.status_code = 200
            with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_1.json") as f:
                r._content = f.read().encode("utf-8")
            return r

        monkeypatch.setattr(requests, "get", lambda x, headers: mock_response())

        global AUTO_CREATE_NEW_PRODUCTS
        global PRODUCT_BLACKLIST_REGEX
        AUTO_CREATE_NEW_PRODUCTS = True
        PRODUCT_BLACKLIST_REGEX = "*-WS$"
        result = api_crawler.update_cisco_eox_database("WS-C2950G-48-EI-WS")

        assert len(result) == 3, "Three products should be imported"
        # every product should contain the following values
        for e in result:
            assert "blacklist" in e
            assert "updated" in e
            assert "created" in e
            assert "PID" in e
            assert "message" in e

            if e["PID"] == "WS-C2950G-48-EI-WS":
                # Nothing is blacklisted, input of an invalid regular expression should not be possible
                assert e["blacklist"] is False
                assert e["updated"] is True
                assert e["created"] is True
                assert type(e["PID"]) == str
                assert e["message"] is None
            else:
                assert e["blacklist"] is False
                assert e["updated"] is True
                assert e["created"] is True
                assert type(e["PID"]) == str
                assert e["message"] is None

        assert Product.objects.count() == 3, "No products are created, because the creation mode is disabled by default"
        AUTO_CREATE_NEW_PRODUCTS = False
        PRODUCT_BLACKLIST_REGEX = ""

    def test_offline_valid_update_cisco_eox_database_with_create_flag_and_multiple_blacklist(self, monkeypatch):
        # mock the underlying GET request
        def mock_response():
            r = Response()
            r.status_code = 200
            with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_1.json") as f:
                r._content = f.read().encode("utf-8")
            return r

        monkeypatch.setattr(requests, "get", lambda x, headers: mock_response())

        global AUTO_CREATE_NEW_PRODUCTS
        global PRODUCT_BLACKLIST_REGEX
        AUTO_CREATE_NEW_PRODUCTS = True
        PRODUCT_BLACKLIST_REGEX = "WS-C2950G-48-EI-WS;WS-C2950G-24-EI"
        result = api_crawler.update_cisco_eox_database("WS-C2950G-48-EI-WS")

        assert len(result) == 3, "Three products should be imported"
        # every product should contain the following values
        for e in result:
            assert "blacklist" in e
            assert "updated" in e
            assert "created" in e
            assert "PID" in e
            assert "message" in e

            if e["PID"] == "WS-C2950G-48-EI-WS" or e["PID"] == "WS-C2950G-24-EI":
                assert e["blacklist"] is True
                assert e["updated"] is False
                assert e["created"] is False
                assert type(e["PID"]) == str
                assert e["message"] is None
            else:
                assert e["blacklist"] is False
                assert e["updated"] is True
                assert e["created"] is True
                assert type(e["PID"]) == str
                assert e["message"] is None

        assert Product.objects.count() == 1, "No products are created, because the creation mode is disabled by default"
        AUTO_CREATE_NEW_PRODUCTS = False
        PRODUCT_BLACKLIST_REGEX = ""
