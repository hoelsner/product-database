import requests
import json
import datetime
import logging
from django.core.cache import cache
from app.config import AppSettings
from app.productdb.extapi.exception import *

logger = logging.getLogger(__name__)


class BaseCiscoApiConsole:
    """
    Basic Cisco API console implementation

    This class will handle the OAuth2 process, get a token from the central authentication directory and caches
    the result in a local file along with the expire date.

    """
    AUTH_TOKEN_CACHE_KEY = "cisco_api_auth_token"
    AUTHENTICATION_URL = "https://cloudsso.cisco.com/as/token.oauth2"

    client_id = None
    client_secret = None

    current_access_token = None
    http_auth_header = None
    token_expire_datetime = datetime.datetime.now()

    # just for testing, indicates, that the class has claimed new token
    __new_token_created__ = False

    def __repr__(self):
        return {
            "cliend_id": self.client_id,
            "http_auth_header": self.http_auth_header,
            "current_access_token": self.current_access_token
        }

    def load_client_credentials(self):
        logger.debug("load client credentials from configuration")
        app_settings = AppSettings()
        app_settings.read_file()

        # load client credentials
        self.client_id = app_settings.get_cisco_api_client_id()
        self.client_secret = app_settings.get_cisco_api_client_secret()

    def save_client_credentials(self):
        logger.warn("DEPRECATED METHOD CALL, use configuration engine instead")
        logger.debug("save new client credentials from configuration")

        app_settings = AppSettings()
        app_settings.read_file()

        app_settings.set_cisco_api_client_id(self.client_id)
        app_settings.set_cisco_api_client_secret(self.client_secret)
        self.drop_cached_token()                                        # drop cached token, new credentials added
        app_settings.write_file()

        logger.info("Client credentials updated")

    def __save_cached_temp_token__(self):
        logger.debug("save token to cache")

        temp_auth_token = dict()
        temp_auth_token['http_auth_header'] = self.http_auth_header
        temp_auth_token['expire_datetime'] = self.token_expire_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")

        cache.set(
            self.AUTH_TOKEN_CACHE_KEY,
            json.dumps(temp_auth_token),
            timeout=self.token_expire_datetime.timestamp()
        )

        logger.info("temporary token saved")

    def __load_cached_temp_token__(self):
        logger.debug("load cached temp token")

        try:
            cached_auth_token = cache.get(self.AUTH_TOKEN_CACHE_KEY)
            if not cached_auth_token:
                return False
            temp_auth_token = json.loads(cached_auth_token)

            self.http_auth_header = temp_auth_token['http_auth_header']
            self.token_expire_datetime = datetime.datetime.strptime(
                temp_auth_token['expire_datetime'],
                "%Y-%m-%d %H:%M:%S.%f"
            )
            return True

        except:
            logger.info("cannot load cached token: register new token")
            return False

    def get_client_credentials(self):
        if self.client_id is None:
            self.load_client_credentials()

        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

    def create_temporary_access_token(self, force_new_token=False):
        logger.debug("create new temporary token")
        if self.client_id is None:
            raise CredentialsNotFoundException("Client credentials not defined/found")

        authz_header = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }

        # check if previous token expired
        if self.__is_cached_token_valid__():
            logger.info("cached token valid, continue with it")

        else:
            logger.info("cached token invalid or not existing (force:%s)" % force_new_token)
            try:
                result = requests.post(self.AUTHENTICATION_URL, params=authz_header)

            except Exception as ex:
                logger.error("cannot contact authentication server at %s" % self.AUTHENTICATION_URL, exc_info=True)
                raise ConnectionFailedException("cannot contact authentication server") from ex

            if result.status_code == 401:
                # unauthorized
                logger.error("cannot claim access token, Invalid client or client credentials")
                raise InvalidClientCredentialsException("Invalid client or client credentials")

            if result.text.find("Not Authorized") != -1:
                logger.error("cannot claim access token, authorization failed")
                raise AuthorizationFailedException("Not Authorized")

            else:
                self.current_access_token = json.loads(result.text)
                self.__new_token_created__ = True

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
        self.__save_cached_temp_token__()

    def drop_cached_token(self):
        cache.delete(self.AUTH_TOKEN_CACHE_KEY)
        self.current_access_token = None
        self.http_auth_header = None

    def __is_cached_token_valid__(self):
        if self.token_expire_datetime is not None:
            logger.debug("check cached token state: %s <= %s" % (datetime.datetime.now(),
                                                                 self.token_expire_datetime))
            return datetime.datetime.now() <= self.token_expire_datetime

        return False

    def is_ready_for_use(self):
        # verify load state
        if self.client_id is None:
            raise CredentialsNotFoundException("credentials not loaded")

        if self.http_auth_header is None:
            # check that a valid token exists
            # renew if required
            if not self.__load_cached_temp_token__():
                self.create_temporary_access_token(force_new_token=True)
            else:
                if not self.__is_cached_token_valid__():
                    logger.info("access token expired, claim new one")
                    self.create_temporary_access_token(force_new_token=True)

        elif not self.__is_cached_token_valid__():
            logger.info("access token expired, claim new one")
            self.create_temporary_access_token(force_new_token=True)

        return True


class CiscoHelloApi(BaseCiscoApiConsole):
    """
    Implementation of the Hello API endpoint for testing

    """
    HELLO_API_URL = "https://api.cisco.com/hello"

    def hello_api_call(self):
        logger.debug("call to Hello API endpoint")
        if self.is_ready_for_use():
            try:
                result = requests.get(self.HELLO_API_URL, headers=self.http_auth_header)
                if result.text.find("Not Authorized") != -1:
                    logger.debug("call not authorized: %s" % result.text)
                    raise AuthorizationFailedException("Not Authorized")

            except Exception as ex:
                logger.error("cannot contact API endpoint at %s" % self.HELLO_API_URL, exc_info=True)
                raise ConnectionFailedException("cannot contact API endpoint at %s" % self.HELLO_API_URL) from ex

            return result.json()
        raise CiscoApiCallFailed("Client not ready (credentials or token missing)")


class CiscoEoxApi(BaseCiscoApiConsole):
    """
    Implementation of the EoX API Version 4 endpoint

    """
    EOX_API_URL = "https://api.cisco.com/supporttools/eox/rest/4/EOXByProductID/%d/%s"

    last_json_result = None
    last_page_call = 0

    def query_product(self, product_id, page=1):
        """

        :param product_id: To enhance search capabilities, the Cisco Support Tools allows wildcards with the productIDs
        parameter. A minimum of 3 characters is required. For example, only the following inputs are valid: *VPN*,
        *VPN, VPN*, and VPN. Using wildcards can result in multiple PIDs in the output.
        :param page: page, that should be called
        :return:
        """
        logger.debug("call to Cisco EoX API endpoint with '%s'" % product_id)
        if self.is_ready_for_use():
            url = self.EOX_API_URL % (page, product_id)
            try:
                result = requests.get(url, headers=self.http_auth_header)
                if result.text.find("Not Authorized") != -1:
                    logger.debug("call not authorized: %s" % result.text)
                    raise AuthorizationFailedException("Not Authorized")

                self.last_json_result = result.json()
                self.last_page_call = page

                # check for API error
                if self.has_api_error():
                    logger.fatal("Cisco EoX API error occured: %s" % self.get_api_error_message())
                    raise CiscoApiCallFailed(self.get_api_error_message())

                return self.last_json_result

            except Exception as ex:
                logger.error("cannot contact API endpoint at %s" % url, exc_info=True)
                raise ConnectionFailedException("cannot contact API endpoint at %s" %
                                                url) from ex

        raise CiscoApiCallFailed("Client not ready (credentials or token missing)")

    def amount_of_pages(self):
        if self.last_json_result is None:
            return 0

        return int(self.last_json_result['PaginationResponseRecord']['LastIndex'])

    def amount_of_total_records(self):
        if self.last_json_result is None:
            return 0

        if int(self.last_json_result['PaginationResponseRecord']['TotalRecords']) == 1:
            return self.get_valid_record_count()

        return int(self.last_json_result['PaginationResponseRecord']['TotalRecords'])

    def get_current_page(self):
        if self.last_json_result is None:
            return 0

        return int(self.last_json_result['PaginationResponseRecord']['PageIndex'])

    def get_valid_record_count(self):
        if self.last_json_result is None:
            return 0
        if len(self.last_json_result['EOXRecord']) == 1:
            if "EOXError" in self.last_json_result['EOXRecord'][0].keys():
                return 0

            else:
                return 1

        else:
            return self.amount_of_total_records()

    def has_api_error(self):
        """Identifies API errors

        :return:
        """
        if "EOXError" in self.last_json_result.keys():
            return True

        return False

    def get_api_error_message(self):
        """returns API error message, if existing in the last query

        :return:
        """
        if "EOXError" in self.last_json_result.keys():
            msg = "%s (%s)" % (self.last_json_result['EOXError']['ErrorDescription'],
                               self.last_json_result['EOXError']['ErrorID'])
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
