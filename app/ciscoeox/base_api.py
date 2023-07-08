import os
import datetime
import json
import logging
from json import JSONDecodeError

import requests
from django.conf import settings
from django.core.cache import cache
from app.ciscoeox.exception import *
from app.config.settings import AppSettings

logger = logging.getLogger("productdb")


class BaseCiscoApiConsole:
    """
    Basic Cisco API implementation

    This class implements the OAuth2 authentication process, get a token from the central authentication directory and
    caches the resulting access token.
    """
    AUTH_TOKEN_CACHE_KEY = "cisco_api_auth_token"
    AUTHENTICATION_URL = ""
    BASE_URL = "https://apix.cisco.com"

    client_id = None
    client_secret = None

    current_access_token = None
    http_auth_header = None
    token_expire_datetime = datetime.datetime.now()
    _session = None

    def __init__(self):
        self.proxies = {
          "http": settings.HTTP_PROXY_SERVER,
          "https": settings.HTTPS_PROXY_SERVER,
        }
        # set to https://cloudsso.cisco.com/as/token.oauth2 for old API version according to
        # https://apiconsole.cisco.com/docs/read/overview/Migrating_Applications
        self.AUTHENTICATION_URL = os.environ.get("CISCO_TOKEN_AUTHENTICATION_URL",
                                                 "https://id.cisco.com/oauth2/default/v1/token")
        # old API URL https://api.cisco.com
        self.BASE_URL = os.environ.get("CISCO_API_BASE_URL",
                                       "https://apix.cisco.com")

    def __del__(self):
        if self._session is not None:
            self._session.close()

    def __repr__(self):
        return "Base Cisco Support API: Client ID %s" % self.client_id

    def __save_cached_temp_token__(self, timeout_seconds):
        logger.debug("save token to cache")

        temp_auth_token = dict()
        temp_auth_token['http_auth_header'] = self.http_auth_header
        temp_auth_token['expire_datetime'] = self.token_expire_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")

        cache.set(
            self.AUTH_TOKEN_CACHE_KEY,
            json.dumps(temp_auth_token),
            timeout=timeout_seconds
        )

        logger.debug("temporary token saved")

    def __load_cached_temp_token__(self):
        logger.debug("load cached temp token")

        try:
            cached_auth_token = cache.get(self.AUTH_TOKEN_CACHE_KEY)
            if not cached_auth_token:
                self.drop_cached_token()        # clean instance
                return False
            temp_auth_token = json.loads(cached_auth_token)

            self.http_auth_header = temp_auth_token['http_auth_header']
            self.token_expire_datetime = datetime.datetime.strptime(
                temp_auth_token['expire_datetime'],
                "%Y-%m-%d %H:%M:%S.%f"
            )
            return True

        except:  # catch any exception
            logger.debug("cannot load cached token: register new token")
            return False

    def __check_response_for_errors__(self, response):
        """check for common errors on the API endpoints"""
        if response.status_code == 401:
            logger.error("cannot claim access token, Invalid client or client credentials (%s)" % response.url)
            raise InvalidClientCredentialsException("Invalid client or client credentials")

        if response.status_code == 500:
            logger.error("API response invalid, result was HTTP 500 (%s)" % response.url)
            raise CiscoApiCallFailed("API response invalid, result was HTTP 500")

        # depending on the API endpoint error contents may vary
        errmsgs = {
            # value to match : error message to raise
            "<h1>Not Authorized</h1>": {
                "log_message": "cannot claim access token, authorization failed (%s)",
                "exception_message": "User authorization failed"
            },
            "<h1>Developer Inactive</h1>": {
                "log_message": "cannot claim access token, developer inactive (%s)",
                "exception_message": "Insufficient Permissions on API endpoint"
            },
            "<h1>Gateway Timeout</h1>": {
                "log_message": "cannot claim access token, Gateway timeout (%s)",
                "exception_message": "API endpoint temporary unreachable"
            }
        }
        for match_value, msgs in errmsgs.items():
            if response.text == match_value or match_value in response.text:
                logger.error(msgs["log_message"] % response.url)
                raise AuthorizationFailedException(msgs["exception_message"])

    def load_client_credentials(self):
        logger.debug("load client credentials from configuration")
        app_settings = AppSettings()

        # load client credentials
        self.client_id = app_settings.get_cisco_api_client_id()
        self.client_secret = app_settings.get_cisco_api_client_secret()

    def get_client_credentials(self):
        if self.client_id is None:
            self.load_client_credentials()

        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

    def create_temporary_access_token(self, force_new_token=False):
        if self.client_id is None:
            raise CredentialsNotFoundException("Client credentials not defined/found")

        authz_header = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }

        # try to load the cached token
        if not self.__load_cached_temp_token__():
            # check if previous token expired
            if self.__is_cached_token_valid__():
                logger.debug("cached token valid, continue with it")

            else:
                logger.debug("cached token invalid or not existing (force:%s)" % force_new_token)
                try:
                    response = requests.post(
                        self.AUTHENTICATION_URL,
                        headers={
                            "accept": "application/json",
                            "content-type": "application/x-www-form-urlencoded",
                        },
                        params=authz_header,
                        proxies=self.proxies
                    )

                except Exception as ex:
                    logger.error("cannot contact authentication server at %s (%s)" % (
                        self.AUTHENTICATION_URL,
                        ex
                    ), exc_info=True)
                    logger.exception(ex)
                    raise ConnectionFailedException("cannot contact authentication server") from ex

                self.__check_response_for_errors__(response)
                try:
                    jdata = response.json()

                except:
                    logger.error("unexpected response from API endpoint (malformed JSON content)")
                    raise CiscoApiCallFailed("unexpected content from API endpoint")

                if type(self.current_access_token) is dict:
                    if "error" in self.current_access_token.keys():
                        logger.error("%s, was returned from the cisco API" % self.current_access_token["error"])
                        raise CiscoApiCallFailed(
                            "error occurred when contacting the cisco API (%s)" % self.current_access_token["error"]
                        )

                cache.delete(self.AUTH_TOKEN_CACHE_KEY)
                self.current_access_token = jdata

                # set expire date
                expire_offset = datetime.timedelta(seconds=self.current_access_token['expires_in'])
                self.token_expire_datetime = datetime.datetime.now() + expire_offset

                self.http_auth_header = {
                    # we will just work with JSON results
                    "Accept": "application/json",
                    "Authorization": "%s %s" % (self.current_access_token['token_type'],
                                                self.current_access_token['access_token']),
                }

                # dump token to temp file
                self.__save_cached_temp_token__(self.current_access_token['expires_in'])

    def drop_cached_token(self):
        cache.delete(self.AUTH_TOKEN_CACHE_KEY)
        self.current_access_token = None
        self.http_auth_header = None
        self.token_expire_datetime = None

    def __is_cached_token_valid__(self):
        result = False
        if self.token_expire_datetime is not None:
            logger.debug("check cached token state: %s <= %s" % (datetime.datetime.now(),
                                                                 self.token_expire_datetime))
            result = datetime.datetime.now() <= self.token_expire_datetime

        return result if result else False

    def is_ready_for_use(self):
        """
        verify the state of the class
        :return:
        """
        if self.client_id is None:
            return False

        if self.http_auth_header is None:
            # check that a valid token exists, renew if required
            if not self.__load_cached_temp_token__():
                self.create_temporary_access_token(force_new_token=True)

        elif not self.__is_cached_token_valid__():
            logger.debug("access token expired, claim new one")
            self.create_temporary_access_token(force_new_token=True)

        return True

    def get_request(self, url):
        if self._session is None:
            self._session = requests.Session()

        try:
            response = self._session.get(url, headers=self.http_auth_header, proxies=self.proxies)

        except Exception as ex:
            logger.error("cannot contact API endpoint at %s" % url, exc_info=True)
            raise ConnectionFailedException("cannot contact API endpoint at %s" % url) from ex

        self.__check_response_for_errors__(response)
        try:
            jdata = response.json()

        except JSONDecodeError as ex:
            logger.warning("url %s doesn't return valid json, returning an empty dictionary instead")
            jdata = {}

        except Exception as ex:
            logger.error("unexpected response from API endpoint (malformed JSON content)")
            logger.exception(ex)
            raise CiscoApiCallFailed("unexpected content from API endpoint")

        return jdata


class CiscoHelloApi(BaseCiscoApiConsole):
    """
    Implementation of the Cisco Hello API endpoint (only for testing)
    """
    HELLO_API_URL = ""

    def __init__(self, *args, **kwargs):
        super(CiscoHelloApi, self).__init__()
        # old URL is https://api.cisco.com/hello
        self.HELLO_API_URL = f"{self.BASE_URL}/hello"

    def hello_api_call(self):
        if self.is_ready_for_use():
            return self.get_request(self.HELLO_API_URL)

        raise CiscoApiCallFailed("Client not ready (credentials or token missing)")


class CiscoEoxApi(BaseCiscoApiConsole):
    """
    Implementation for the Cisco EoX API Version 5 endpoint
    """
    EOX_API_URL = ""
    EOX_YEAR_API_URL = ""
    last_json_result = None
    last_page_call = 0

    def __init__(self):
        super(CiscoEoxApi, self).__init__()
        self.EOX_API_URL = f"{self.BASE_URL}/supporttools/eox/rest/5/EOXByProductID/%d/%s"
        self.EOX_YEAR_API_URL = f"{self.BASE_URL}/supporttools/eox/rest/5/EOXByDates/" \
                                "%(pageIndex)d/%(startDate)s/%(endDate)s"

    def query_product(self, product_id, page=1):
        """
        :param product_id: To enhance search capabilities, the Cisco Support Tools allows wildcards with the productIDs
        parameter. A minimum of 3 characters is required. For example, only the following inputs are valid: *VPN*,
        *VPN, VPN*, and VPN. Using wildcards can result in multiple PIDs in the output.
        :param page: page, that should be called
        :return:
        """
        logger.debug("call to Cisco EoX API endpoint with '%s' on page %d" % (product_id, page))
        if self.is_ready_for_use():
            url = self.EOX_API_URL % (page, product_id)
            self.last_json_result = self.get_request(url)
            self.last_page_call = page

            # check for API error
            if self.has_api_error():
                # if the API error message only states that no EoX information are available, just return nothing
                if not self.get_api_error_message().startswith("Incorrect PID:") and not self.get_api_error_message().startswith("EOX information does not exist for the following product ID(s):"):
                    msg = "Cisco EoX API error: %s" % self.get_api_error_message()
                    logger.fatal(msg)
                    raise CiscoApiCallFailed(msg)

            return self.last_json_result

        raise CiscoApiCallFailed("Client not ready (credentials or token missing)")

    def query_year(self, year_to_query, page=1):
        """
        query products that are EoL announced in a specific year
        :param year_to_query: year that should be used (e.g. 2017)
        :param page:
        :return:
        """
        logger.debug("call to Cisco EoX API endpoint for year '%s' on page %d" % (year_to_query, page))
        if self.is_ready_for_use():
            url = self.EOX_YEAR_API_URL % {
                "pageIndex": page,
                "startDate": "%d-01-01" % year_to_query,
                "endDate": "%d-12-31" % year_to_query
            }
            self.last_json_result = self.get_request(url)
            self.last_page_call = page

            # check for API error
            if self.has_api_error():
                # if the API error message only states that no EoX information are available, just return nothing
                if not self.get_api_error_message().startswith("EOX information does not exist for the following "
                                                               "product ID(s):"):
                    msg = "Cisco EoX API error: %s" % self.get_api_error_message()
                    logger.fatal(msg)
                    raise CiscoApiCallFailed(msg)

            return self.last_json_result

        raise CiscoApiCallFailed("Client not ready (credentials or token missing)")

    def amount_of_pages(self):
        if self.last_json_result is None:
            return 0

        if "PaginationResponseRecord" in self.last_json_result.keys():
            return int(self.last_json_result['PaginationResponseRecord']['LastIndex'])

        return 1

    def amount_of_total_records(self):
        if self.last_json_result is None:
            return 0

        if "PaginationResponseRecord" in self.last_json_result.keys():
            if int(self.last_json_result['PaginationResponseRecord']['TotalRecords']) == 1:
                return self.get_page_record_count()

            else:
                return int(self.last_json_result['PaginationResponseRecord']['TotalRecords'])

        else:
            return 0

    def get_current_page(self):
        if self.last_json_result is None:
            return 0

        if "PaginationResponseRecord" in self.last_json_result.keys():
            return int(self.last_json_result['PaginationResponseRecord']['PageIndex'])

        return 1

    def get_page_record_count(self):
        if self.last_json_result is None:
            return 0

        if len(self.last_json_result['EOXRecord']) == 1:
            if "EOXError" in self.last_json_result['EOXRecord'][0].keys():
                return 0

            else:
                return 1

        else:
            return len(self.last_json_result['EOXRecord'])

    def has_api_error(self):
        """
        identifies API errors
        :return:
        """
        if self.has_error(self.last_json_result["EOXRecord"][0]):
            return True

        return False

    def get_api_error_message(self):
        """
        returns API error message, if existing in the last query
        :return:
        """
        if self.has_error(self.last_json_result["EOXRecord"][0]):
            msg = "%s (%s)" % (self.get_error_description(self.last_json_result["EOXRecord"][0]),
                               self.last_json_result["EOXRecord"][0]['EOXError']['ErrorID'])
            return msg

        return "no error"

    @staticmethod
    def has_error(record):
        if "EOXError" in record.keys():
            return True

        else:
            return False

    @staticmethod
    def get_error_description(record):
        if "EOXError" in record.keys():
            return record['EOXError']['ErrorDescription']

        else:
            return ""

    def get_eox_records(self):
        """
        returns a list with all records from the current page.
        The record format for API version 4 is the following:
        :return:
        """
        if self.last_json_result is None:
            return []

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("results from Cisco EoX database: %s" % json.dumps(self.last_json_result, indent=4))

        return self.last_json_result['EOXRecord']
