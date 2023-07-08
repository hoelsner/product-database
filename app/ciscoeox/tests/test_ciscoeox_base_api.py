"""
Test suite for the ciscoeox.base_api module
"""
import datetime
import json
import os
import pytest
import requests
from requests.models import Response
from app.ciscoeox import base_api
from app.ciscoeox.base_api import CiscoHelloApi, CiscoApiCallFailed, CredentialsNotFoundException, \
    InvalidClientCredentialsException, ConnectionFailedException, AuthorizationFailedException, CiscoEoxApi
from django.core.cache import cache

pytestmark = pytest.mark.django_db


class BaseCiscoApiConsoleSettings:
    """
    Mock object that provides the Cisco API credentials used for online tests. If no credentials are found, dummy
    values are used.
    """
    CREDENTIALS_FILE = ".cisco_api_credentials"

    def read_file(self):
        pass

    def load_client_credentials(self):
        pass

    def is_cisco_api_enabled(self):
        return True

    def close(self):
        pass

    def get_cisco_api_client_id(self):
        return os.getenv("TEST_CISCO_API_CLIENT_ID", "dummy_id")

    def get_cisco_api_client_secret(self):
        return os.getenv("TEST_CISCO_API_CLIENT_SECRET", "dummy_secret")


def mock_access_token_generation():
    temp_auth_token = {}
    temp_auth_token['http_auth_header'] = "mock header"
    temp_auth_token['expire_datetime'] = datetime.datetime(year=2050, month=1, day=1).isoformat()

    cache.set(
        CiscoHelloApi.AUTH_TOKEN_CACHE_KEY,
        json.dumps(temp_auth_token),
        timeout=datetime.datetime(year=2050, month=1, day=1).timestamp()
    )


@pytest.fixture
def use_test_api_configuration(monkeypatch):
    monkeypatch.setattr(base_api, "AppSettings", BaseCiscoApiConsoleSettings)


class TestCiscoHelloApi:
    """Test of the Cisco Hello API class, test also the functionality of the base class"""

    @pytest.mark.usefixtures("use_test_api_configuration")
    @pytest.mark.online
    def test_base_functionality(self):
        cisco_hello_api = CiscoHelloApi()
        assert cisco_hello_api.is_ready_for_use() is False

        assert cisco_hello_api.client_id is None
        assert cisco_hello_api.client_secret is None

        with pytest.raises(CredentialsNotFoundException):
            cisco_hello_api.create_temporary_access_token()

        cisco_hello_api.load_client_credentials()
        assert cisco_hello_api.client_id != "dummy_id", "Should contain valid test credentials"
        assert cisco_hello_api.client_id != "dummy_secret", "Should contain valid test credentials"

        # create a temporary access token
        cisco_hello_api.create_temporary_access_token()
        assert cisco_hello_api.current_access_token is not None
        assert cache.get(CiscoHelloApi.AUTH_TOKEN_CACHE_KEY, None) is not None, "Cached value should be created"

        # test that the class is now ready to use
        assert cisco_hello_api.is_ready_for_use() is True

        # test automatic recreation of the http_auth_header if no cached temp token is available
        cisco_hello_api.http_auth_header = None
        cache.delete(CiscoHelloApi.AUTH_TOKEN_CACHE_KEY)
        assert cisco_hello_api.is_ready_for_use() is True
        assert cisco_hello_api.http_auth_header is not None

        # try to recreate it
        token_before = cisco_hello_api.current_access_token
        cisco_hello_api.create_temporary_access_token()
        assert cisco_hello_api.current_access_token == token_before

        # force the recreation of the token
        cisco_hello_api.current_access_token = {
            "token_type": "my dummy value",
            "access_token": "my dummy value"
        }  # manually overwrite it to see that something happens
        cisco_hello_api.create_temporary_access_token(force_new_token=True)
        assert cisco_hello_api.current_access_token != "my dummy value"

        # cleanup
        cisco_hello_api.drop_cached_token()
        assert cisco_hello_api.current_access_token is None
        assert cache.get(CiscoHelloApi.AUTH_TOKEN_CACHE_KEY, None) is None, "Cached value should be removed"

        # try to drop it again (nothing should happen)
        cisco_hello_api.drop_cached_token()

    @pytest.mark.usefixtures("use_test_api_configuration")
    @pytest.mark.online
    def test_read_from_cached_token(self):
        cisco_hello_api_one = CiscoHelloApi()
        cisco_hello_api_one.load_client_credentials()
        cisco_hello_api_one.create_temporary_access_token()

        assert cache.get(CiscoHelloApi.AUTH_TOKEN_CACHE_KEY, None) is not None

        cisco_hello_api_two = CiscoHelloApi()
        cisco_hello_api_two.load_client_credentials()
        cisco_hello_api_two.create_temporary_access_token()  # should load from cache

        assert cisco_hello_api_one.http_auth_header == cisco_hello_api_two.http_auth_header

    @pytest.mark.usefixtures("use_test_api_configuration")
    def test_automatic_load_of_the_client_credentials(self):
        cisco_hello_api = CiscoHelloApi()
        assert cisco_hello_api.is_ready_for_use() is False

        assert cisco_hello_api.client_id is None
        assert cisco_hello_api.client_secret is None

        cisco_hello_api.get_client_credentials()

        assert cisco_hello_api.client_id is not None
        assert cisco_hello_api.client_secret is not None

    @pytest.mark.usefixtures("use_test_api_configuration")
    @pytest.mark.online
    def test_automatic_renew_of_expired_token(self):
        cisco_hello_api = CiscoHelloApi()
        cisco_hello_api.load_client_credentials()
        cisco_hello_api.create_temporary_access_token()

        # test automatic recreation of the http_auth_header if the cached token was expired
        cisco_hello_api.token_expire_datetime = datetime.datetime.now()
        assert cisco_hello_api.is_ready_for_use() is True
        assert cisco_hello_api.http_auth_header is not None

    def test_invalid_login(self, monkeypatch):
        def get_invalid_authentication_response():
            r = Response()
            r.status_code = 401
            return r

        monkeypatch.setattr(requests, "post", lambda x, params, proxies=None, headers=None: get_invalid_authentication_response())

        cisco_hello_api = CiscoHelloApi()
        cisco_hello_api.load_client_credentials()

        with pytest.raises(InvalidClientCredentialsException) as exinfo:
            cisco_hello_api.create_temporary_access_token()
        assert exinfo.match("Invalid client or client credentials")

    def test_endpoint_unreachable(self, monkeypatch):
        def get_invalid_authentication_response():
            raise Exception()

        monkeypatch.setattr(requests, "post", lambda x, params: get_invalid_authentication_response())

        cisco_hello_api = CiscoHelloApi()
        cisco_hello_api.load_client_credentials()

        with pytest.raises(ConnectionFailedException) as exinfo:
            cisco_hello_api.create_temporary_access_token()
        assert exinfo.match("cannot contact authentication server")

    def test_authorization_error(self, monkeypatch):
        def get_invalid_authentication_response():
            r = Response()
            r.status_code = 200
            r._content = "<h1>Not Authorized</h1>".encode("utf-8")
            return r

        monkeypatch.setattr(requests, "post", lambda x, params, proxies=None, headers=None: get_invalid_authentication_response())

        cisco_hello_api = CiscoHelloApi()
        cisco_hello_api.load_client_credentials()

        with pytest.raises(AuthorizationFailedException) as exinfo:
            cisco_hello_api.create_temporary_access_token()
        assert exinfo.match("User authorization failed")

    def test_authorization_error_alternate_format(self, monkeypatch):
        def get_invalid_authentication_response():
            r = Response()
            r.status_code = 200
            r._content = """\
<html>

<body>
    <h1>Not Authorized</h1>
</body>

</html>
""".encode("utf-8")
            return r

        monkeypatch.setattr(requests, "post", lambda x, params, proxies=None, headers=None: get_invalid_authentication_response())

        cisco_hello_api = CiscoHelloApi()
        cisco_hello_api.load_client_credentials()

        with pytest.raises(AuthorizationFailedException) as exinfo:
            cisco_hello_api.create_temporary_access_token()
        assert exinfo.match("User authorization failed")

    def test_developer_inactive(self, monkeypatch):
        def get_invalid_authentication_response():
            r = Response()
            r.status_code = 200
            r._content = "<h1>Developer Inactive</h1>".encode("utf-8")
            return r

        monkeypatch.setattr(requests, "post", lambda x, params, proxies=None, headers=None: get_invalid_authentication_response())

        cisco_hello_api = CiscoHelloApi()
        cisco_hello_api.load_client_credentials()

        with pytest.raises(AuthorizationFailedException) as exinfo:
            cisco_hello_api.create_temporary_access_token()
        assert exinfo.match("Insufficient Permissions on API endpoint")

    def test_developer_inactive_alternate_format(self, monkeypatch):
        def get_invalid_authentication_response():
            r = Response()
            r.status_code = 200
            r._content = """\
<html>

<body>
    <h1>Developer Inactive</h1>
</body>

</html>
""".encode("utf-8")
            return r

        monkeypatch.setattr(requests, "post", lambda x, params, proxies=None, headers=None: get_invalid_authentication_response())

        cisco_hello_api = CiscoHelloApi()
        cisco_hello_api.load_client_credentials()

        with pytest.raises(AuthorizationFailedException) as exinfo:
            cisco_hello_api.create_temporary_access_token()
        assert exinfo.match("Insufficient Permissions on API endpoint")

    def test_api_500(self, monkeypatch):
        def get_invalid_authentication_response():
            r = Response()
            r.status_code = 500
            r._content = "".encode("utf-8")
            return r

        monkeypatch.setattr(requests, "post", lambda x, params, proxies=None, headers=None: get_invalid_authentication_response())

        cisco_hello_api = CiscoHelloApi()
        cisco_hello_api.load_client_credentials()

        with pytest.raises(CiscoApiCallFailed) as exinfo:
            cisco_hello_api.create_temporary_access_token()
        assert exinfo.match("API response invalid, result was HTTP 500")

    def test_gateway_timeout(self, monkeypatch):
        def get_invalid_authentication_response():
            r = Response()
            r.status_code = 200
            r._content = "<h1>Gateway Timeout</h1>".encode("utf-8")
            return r

        monkeypatch.setattr(requests, "post", lambda x, params, proxies=None, headers=None: get_invalid_authentication_response())

        cisco_hello_api = CiscoHelloApi()
        cisco_hello_api.load_client_credentials()

        with pytest.raises(AuthorizationFailedException) as exinfo:
            cisco_hello_api.create_temporary_access_token()
        assert exinfo.match("API endpoint temporary unreachable")

    def test_gateway_timeout_alternate_format(self, monkeypatch):
        def get_invalid_authentication_response():
            r = Response()
            r.status_code = 200
            r._content = """\
<html>

<body>
    <h1>Gateway Timeout</h1>
</body>

</html>
""".encode("utf-8")
            return r

        monkeypatch.setattr(requests, "post", lambda x, params, proxies=None, headers=None: get_invalid_authentication_response())

        cisco_hello_api = CiscoHelloApi()
        cisco_hello_api.load_client_credentials()

        with pytest.raises(AuthorizationFailedException) as exinfo:
            cisco_hello_api.create_temporary_access_token()
        assert exinfo.match("API endpoint temporary unreachable")

    def test_invalid_json(self, monkeypatch):
        def get_invalid_authentication_response():
            r = Response()
            r.status_code = 200
            r._content = "My invalid JSON string".encode("utf-8")
            return r

        monkeypatch.setattr(requests, "post", lambda x, params, proxies=None, headers=None: get_invalid_authentication_response())

        cisco_hello_api = CiscoHelloApi()
        cisco_hello_api.load_client_credentials()

        with pytest.raises(CiscoApiCallFailed) as exinfo:
            cisco_hello_api.create_temporary_access_token()
        assert exinfo.match("unexpected content from API endpoint")

    @pytest.mark.usefixtures("use_test_api_configuration")
    @pytest.mark.online
    def test_online_hello_api_call(self):
        cisco_hello_api = CiscoHelloApi()
        cisco_hello_api.load_client_credentials()
        cisco_hello_api.create_temporary_access_token()

        json_result = cisco_hello_api.hello_api_call()

        assert isinstance(json_result, dict)

    def test_offline_hello_api_call(self, monkeypatch):
        class MockSession:
            def get(self, *args, **kwargs):
                r = Response()
                r.status_code = 200
                r._content = json.dumps({'helloResponse': {'response': 'Hello World!'}}).encode("utf-8")
                return r

        monkeypatch.setattr(requests, "Session", MockSession)

        cisco_hello_api = CiscoHelloApi()
        monkeypatch.setattr(cisco_hello_api, "create_temporary_access_token",
                            lambda force_new_token=True: mock_access_token_generation())

        with pytest.raises(CiscoApiCallFailed) as exinfo:
            cisco_hello_api.hello_api_call()
        assert exinfo.match("Client not ready")

        cisco_hello_api.load_client_credentials()
        cisco_hello_api.create_temporary_access_token()

        json_result = cisco_hello_api.hello_api_call()
        assert isinstance(json_result, dict)

    def test_offline_hello_api_call_with_connection_issue(self, monkeypatch):
        class MockSession:
            def get(self, *args, **kwargs):
                raise Exception()

        monkeypatch.setattr(requests, "Session", MockSession)

        cisco_hello_api = CiscoHelloApi()
        monkeypatch.setattr(cisco_hello_api, "create_temporary_access_token",
                            lambda force_new_token=True: mock_access_token_generation())
        cisco_hello_api.load_client_credentials()
        cisco_hello_api.create_temporary_access_token()

        with pytest.raises(ConnectionFailedException) as exinfo:
            cisco_hello_api.hello_api_call()
        assert exinfo.match("cannot contact API endpoint at")


class TestCiscoEoxApi:
    TEST_QUERY = "WS-C2950G-48-EI"
    TEST_YEAR = 2017
    EXPECTED_VALID_TEST_QUERY_RESPONSE = {
        "EOXRecord": [
            {
                "LinkToProductBulletinURL": "http://www.cisco.com/en/US/products/hw/switches/ps628/prod_eol_notice"
                                            "0900aecd804658c9.html",
                "EndOfRoutineFailureAnalysisDate": {
                    "value": "2007-12-31",
                    "dateFormat": "YYYY-MM-DD"
                },
                "EOXExternalAnnouncementDate": {
                    "value": "2006-04-17",
                    "dateFormat": "YYYY-MM-DD"
                },
                "EndOfServiceContractRenewal": {
                    "value": "2011-03-31",
                    "dateFormat": "YYYY-MM-DD"
                },
                "LastDateOfSupport": {
                    "value": "2011-12-31",
                    "dateFormat": "YYYY-MM-DD"
                },
                "EndOfSvcAttachDate": {
                    "value": "2007-12-31",
                    "dateFormat": "YYYY-MM-DD"
                },
                "EOXInputValue": "WS-C2950G-48-EI ",
                "EOXMigrationDetails": {
                    "MigrationOption": "Enter PID(s)",
                    "MigrationProductName": "",
                    "PIDActiveFlag": "Y",
                    "MigrationProductId": "WS-C2960G-48TC-L",
                    "MigrationProductInfoURL": "",
                    "MigrationInformation": "^Catalyst 2960 48 10/100/1000,  4 T/SFP  LAN Base Image",
                    "MigrationStrategy": ""
                },
                "ProductBulletinNumber": "EOL1094",
                "EOLProductID": "WS-C2950G-48-EI",
                "UpdatedTimeStamp": {
                    "value": "2015-08-14",
                    "dateFormat": "YYYY-MM-DD"
                },
                "EndOfSaleDate": {
                    "value": "2006-12-31",
                    "dateFormat": "YYYY-MM-DD"
                },
                "ProductIDDescription": "Catalyst 2950, 48 10/100 with 2 GBIC slots, Enhanced Image",
                "EOXInputType": "ShowEOXByPids",
                "EndOfSWMaintenanceReleases": {
                    "value": "",
                    "dateFormat": "YYYY-MM-DD"
                },
                "EndOfSecurityVulSupportDate": {
                    "value": "",
                    "dateFormat": "YYYY-MM-DD"
                }
            }
        ],
        "PaginationResponseRecord": {
            "TotalRecords": 1,
            "PageIndex": 1,
            "PageRecords": 1,
            "LastIndex": 1
        }
    }

    @pytest.mark.usefixtures("use_test_api_configuration")
    @pytest.mark.online
    def test_online_query_product_single_page_results(self):
        cisco_eox_api = CiscoEoxApi()
        cisco_eox_api.load_client_credentials()
        cisco_eox_api.create_temporary_access_token()

        assert cisco_eox_api.get_eox_records() == []
        assert cisco_eox_api.amount_of_pages() == 0
        assert cisco_eox_api.get_current_page() == 0
        assert cisco_eox_api.amount_of_total_records() == 0
        assert cisco_eox_api.get_page_record_count() == 0

        jresult = cisco_eox_api.query_product(self.TEST_QUERY, 1)

        assert "EOXRecord" in jresult
        assert "PaginationResponseRecord" in jresult
        assert len(jresult["EOXRecord"]) == 1
        assert cisco_eox_api.get_eox_records() == jresult["EOXRecord"]
        assert cisco_eox_api.amount_of_pages() == 1
        assert cisco_eox_api.get_current_page() == 1
        assert cisco_eox_api.amount_of_total_records() == 1
        assert cisco_eox_api.get_page_record_count() == 1
        assert cisco_eox_api.has_api_error() is False
        assert cisco_eox_api.get_api_error_message() == "no error"
        assert cisco_eox_api.get_error_description(jresult["EOXRecord"][0]) == ""
        assert cisco_eox_api.get_error_description(jresult["EOXRecord"][0]) == ""
        assert self.EXPECTED_VALID_TEST_QUERY_RESPONSE == jresult
        assert cisco_eox_api.get_eox_records() == self.EXPECTED_VALID_TEST_QUERY_RESPONSE["EOXRecord"]

    def test_offline_query_product_single_page_results(self, monkeypatch):
        class MockSession:
            def get(self, *args, **kwargs):
                r = Response()
                r.status_code = 200
                with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_1.json") as f:
                    r._content = f.read().encode("utf-8")
                return r

        monkeypatch.setattr(requests, "Session", MockSession)

        cisco_eox_api = CiscoEoxApi()
        monkeypatch.setattr(cisco_eox_api, "create_temporary_access_token",
                            lambda force_new_token=True: mock_access_token_generation())
        cisco_eox_api.load_client_credentials()
        cisco_eox_api.create_temporary_access_token()

        assert cisco_eox_api.get_eox_records() == []
        assert cisco_eox_api.amount_of_pages() == 0
        assert cisco_eox_api.get_current_page() == 0
        assert cisco_eox_api.amount_of_total_records() == 0
        assert cisco_eox_api.get_page_record_count() == 0

        jresult = cisco_eox_api.query_product(self.TEST_QUERY, 1)

        assert "EOXRecord" in jresult
        assert "PaginationResponseRecord" in jresult
        assert len(jresult["EOXRecord"]) == 3
        assert cisco_eox_api.get_eox_records() == jresult["EOXRecord"]
        assert cisco_eox_api.amount_of_pages() == 1
        assert cisco_eox_api.get_current_page() == 1
        assert cisco_eox_api.amount_of_total_records() == 3
        assert cisco_eox_api.get_page_record_count() == 3
        assert cisco_eox_api.has_api_error() is False
        assert cisco_eox_api.get_api_error_message() == "no error"
        assert cisco_eox_api.get_error_description(jresult["EOXRecord"][0]) == ""
        assert cisco_eox_api.get_error_description(jresult["EOXRecord"][0]) == ""

    def test_offline_query_product_multiple_page_results(self, monkeypatch):
        class MockSessionPageOne:
            _first_call = False

            def get(self, *args, **kwargs):
                r = Response()
                r.status_code = 200
                if not self._first_call:
                    with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_2.json") as f:
                        r._content = f.read().encode("utf-8")
                    self._first_call = True

                else:
                    with open("app/ciscoeox/tests/data/cisco_eox_response_page_2_of_2.json") as f:
                        r._content = f.read().encode("utf-8")

                return r

        monkeypatch.setattr(requests, "Session", MockSessionPageOne)

        cisco_eox_api = CiscoEoxApi()
        monkeypatch.setattr(cisco_eox_api, "create_temporary_access_token",
                            lambda force_new_token=True: mock_access_token_generation())
        cisco_eox_api.load_client_credentials()
        cisco_eox_api.create_temporary_access_token()

        assert cisco_eox_api.get_eox_records() == []
        assert cisco_eox_api.amount_of_pages() == 0
        assert cisco_eox_api.get_current_page() == 0
        assert cisco_eox_api.amount_of_total_records() == 0
        assert cisco_eox_api.get_page_record_count() == 0

        jresult = cisco_eox_api.query_product(self.TEST_QUERY, 1)

        assert "EOXRecord" in jresult
        assert "PaginationResponseRecord" in jresult
        assert len(jresult["EOXRecord"]) == 2
        assert cisco_eox_api.get_eox_records() == jresult["EOXRecord"]
        assert cisco_eox_api.amount_of_pages() == 2
        assert cisco_eox_api.get_current_page() == 1
        assert cisco_eox_api.amount_of_total_records() == 3
        assert cisco_eox_api.get_page_record_count() == 2
        assert cisco_eox_api.has_api_error() is False
        assert cisco_eox_api.get_api_error_message() == "no error"
        assert cisco_eox_api.get_error_description(jresult["EOXRecord"][0]) == ""
        assert cisco_eox_api.get_error_description(jresult["EOXRecord"][0]) == ""

        jresult = cisco_eox_api.query_product(self.TEST_QUERY, 2)

        assert "EOXRecord" in jresult
        assert "PaginationResponseRecord" in jresult
        assert len(jresult["EOXRecord"]) == 1
        assert cisco_eox_api.get_eox_records() == jresult["EOXRecord"]
        assert cisco_eox_api.amount_of_pages() == 2
        assert cisco_eox_api.get_current_page() == 2
        assert cisco_eox_api.amount_of_total_records() == 3
        assert cisco_eox_api.get_page_record_count() == 1
        assert cisco_eox_api.has_api_error() is False
        assert cisco_eox_api.get_api_error_message() == "no error"
        assert cisco_eox_api.get_error_description(jresult["EOXRecord"][0]) == ""
        assert cisco_eox_api.get_error_description(jresult["EOXRecord"][0]) == ""

    @pytest.mark.usefixtures("use_test_api_configuration")
    @pytest.mark.online
    def test_online_query_product_no_results(self):
        cisco_eox_api = CiscoEoxApi()

        with pytest.raises(CiscoApiCallFailed):
            cisco_eox_api.query_product("NOTHING", 1)

        cisco_eox_api.load_client_credentials()
        cisco_eox_api.create_temporary_access_token()

        assert cisco_eox_api.amount_of_pages() == 0
        assert cisco_eox_api.get_current_page() == 0
        assert cisco_eox_api.amount_of_total_records() == 0
        assert cisco_eox_api.get_page_record_count() == 0

        _ = cisco_eox_api.query_product("NOTHING", 1)

        assert cisco_eox_api.amount_of_pages() == 1
        assert cisco_eox_api.get_current_page() == 1
        assert cisco_eox_api.amount_of_total_records() == 0
        assert cisco_eox_api.get_page_record_count() == 0
        assert cisco_eox_api.has_api_error() is True
        assert cisco_eox_api.get_api_error_message() == "Incorrect PID: [NOTHING] (SSA_ERR_021_Pid)"

    def test_offline_query_product_no_results(self, monkeypatch):
        class MockSession:
            def get(self, *args, **kwargs):
                r = Response()
                r.status_code = 200
                with open("app/ciscoeox/tests/data/cisco_eox_no_result_response.json") as f:
                    r._content = f.read().encode("utf-8")
                return r

        monkeypatch.setattr(requests, "Session", MockSession)

        cisco_eox_api = CiscoEoxApi()
        monkeypatch.setattr(cisco_eox_api, "create_temporary_access_token",
                            lambda force_new_token=True: mock_access_token_generation())

        with pytest.raises(CiscoApiCallFailed):
            cisco_eox_api.query_product("NOTHING", 1)

        cisco_eox_api.load_client_credentials()
        cisco_eox_api.create_temporary_access_token()

        assert cisco_eox_api.amount_of_pages() == 0
        assert cisco_eox_api.get_current_page() == 0
        assert cisco_eox_api.amount_of_total_records() == 0
        assert cisco_eox_api.get_page_record_count() == 0

        _ = cisco_eox_api.query_product("NOTHING", 1)

        assert cisco_eox_api.amount_of_pages() == 1
        assert cisco_eox_api.get_current_page() == 1
        assert cisco_eox_api.amount_of_total_records() == 0
        assert cisco_eox_api.get_page_record_count() == 0
        assert cisco_eox_api.has_api_error() is True
        assert cisco_eox_api.get_api_error_message() == "EOX information does not exist for the following product " \
                                                        "ID(s): NOTHING (SSA_ERR_026)"

    def test_offline_query_year(self, monkeypatch):
        class MockSession:
            def get(self, *args, **kwargs):
                r = Response()
                r.status_code = 200
                with open("app/ciscoeox/tests/data/cisco_eox_response_page_1_of_1.json") as f:
                    r._content = f.read().encode("utf-8")
                return r

        monkeypatch.setattr(requests, "Session", MockSession)

        cisco_eox_api = CiscoEoxApi()
        monkeypatch.setattr(cisco_eox_api, "create_temporary_access_token",
                            lambda force_new_token=True: mock_access_token_generation())
        cisco_eox_api.load_client_credentials()
        cisco_eox_api.create_temporary_access_token()

        assert cisco_eox_api.get_eox_records() == []
        assert cisco_eox_api.amount_of_pages() == 0
        assert cisco_eox_api.get_current_page() == 0
        assert cisco_eox_api.amount_of_total_records() == 0
        assert cisco_eox_api.get_page_record_count() == 0

        jresult = cisco_eox_api.query_year(self.TEST_YEAR, 1)

        assert "EOXRecord" in jresult
        assert "PaginationResponseRecord" in jresult
        assert len(jresult["EOXRecord"]) == 3
        assert cisco_eox_api.get_eox_records() == jresult["EOXRecord"]
        assert cisco_eox_api.amount_of_pages() == 1
        assert cisco_eox_api.get_current_page() == 1
        assert cisco_eox_api.amount_of_total_records() == 3
        assert cisco_eox_api.get_page_record_count() == 3
        assert cisco_eox_api.has_api_error() is False
        assert cisco_eox_api.get_api_error_message() == "no error"
        assert cisco_eox_api.get_error_description(jresult["EOXRecord"][0]) == ""
        assert cisco_eox_api.get_error_description(jresult["EOXRecord"][0]) == ""

    @pytest.mark.usefixtures("use_test_api_configuration")
    @pytest.mark.online
    def test_online_query_year(self):
        cisco_eox_api = CiscoEoxApi()

        with pytest.raises(CiscoApiCallFailed):
            cisco_eox_api.query_year(self.TEST_YEAR, 1)

        cisco_eox_api.load_client_credentials()
        cisco_eox_api.create_temporary_access_token()

        assert cisco_eox_api.amount_of_pages() == 0
        assert cisco_eox_api.get_current_page() == 0
        assert cisco_eox_api.amount_of_total_records() == 0
        assert cisco_eox_api.get_page_record_count() == 0

        _ = cisco_eox_api.query_year(self.TEST_YEAR, 1)

        # the response for the year is not stable over time, so just check that something was provided
        assert cisco_eox_api.amount_of_pages() > 2
        assert cisco_eox_api.get_current_page() == 1
        assert cisco_eox_api.amount_of_total_records() >= 1001
        assert cisco_eox_api.get_page_record_count() == 1000
        assert cisco_eox_api.has_api_error() is False

