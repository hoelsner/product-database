"""
Settings file class for the product database
"""
import configparser
import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)


class AppSettings:
    """
    Product Database settings
    """
    CONFIG_FILE_NAME = None

    GLOBAL_SECTION = "global"
    CISCO_API_SECTION = "cisco_api"
    CISCO_EOX_CRAWLER_SECTION = "cisco_eox_api_crawler"

    # static defined defaults for the application
    CONFIG_DEFAULTS = {
        GLOBAL_SECTION: {
            "cisco_api_enabled": "false"
        },
        CISCO_API_SECTION: {
            "client_id": "",
            "client_secret": "",
            "cisco_api_credentials_successful_tested": "false",
            "cisco_api_credentials_last_message": "not tested"
        },
        CISCO_EOX_CRAWLER_SECTION: {
            "periodic_sync_enabled": "false",
            "auto_create_new_products": "false",
            "eox_api_queries": "",
            "product_blacklist_regex": "",
            "eox_api_sync_task_id": "",
            "eox_api_auto_sync_last_execution_time": "",
            "eox_api_auto_sync_last_execution_result": ""
        }
    }
    # instance of the ConfigParser
    _parser = None

    def __init__(self):
        # use the config file name that is defined in the Django configuration
        self.CONFIG_FILE_NAME = settings.APP_CONFIG_FILE

    def to_dictionary(self):
        result = {}

        for section in self._parser.sections():
            result[section] = {}
            for key, val in self._parser.items(section):
                result[section][key] = val

        return result

    def create_defaults(self):
        """
        create default configuration file
        """
        self._parser = configparser.ConfigParser()
        self._parser.update(self.CONFIG_DEFAULTS)

        try:
            with open(self.CONFIG_FILE_NAME, "w") as file:
                self._parser.write(file)

        except:
            logger.error("cannot create default configuration file", exc_info=True)
            raise

    def file_exists(self):
        """
        check if the configuration file exist
        """
        return os.path.exists(self.CONFIG_FILE_NAME)

    def read_file(self):
        """
        read the configuration file based on the given config file name

        if the file don't exist, create a default configuration file
        """
        if self.file_exists():
            self._parser = configparser.ConfigParser()
            self._parser.update(self.CONFIG_DEFAULTS)
            self._parser.read(self.CONFIG_FILE_NAME)
        else:
            self.create_defaults()

    def write_file(self):
        """
        save current configuration
        """
        try:
            with open(self.CONFIG_FILE_NAME, "w") as file:
                self._parser.write(file)

        except:
            logger.error("cannot write configuration file", exc_info=True)
            raise

    def get_string(self, key, section=GLOBAL_SECTION, default=None):
        """
        wrapper for the configparser get method
        """
        return self._parser.get(section=section, option=key, fallback=default)

    def get_boolean(self, key, section=GLOBAL_SECTION, default=None):
        """
        wrapper for the configparser getboolean method
        """
        return self._parser.getboolean(section=section, option=key, fallback=default)

    def set(self, value, key, section=GLOBAL_SECTION):
        """
        wrapper for the configparser set method
        """
        # ensure, that the value is a string
        if type(value) is not str:
            value = str(value)

        return self._parser.set(section=section, option=key, value=value)

    ####################################################################################################################
    # predefined configuration options

    def is_cisco_api_enabled(self):
        """
        True if the Cisco API is enabled in the configuration, otherwise False
        """
        return self.get_boolean("cisco_api_enabled", default=False)

    def set_cisco_api_enabled(self, value):
        """
        enable/disable the Cisco API access
        """
        if type(value) is not bool:
            raise ValueError("Value for the Cisco API enable must be boolean")

        self._parser.set(option="cisco_api_enabled", section=self.GLOBAL_SECTION, value=str(value))

    def is_periodic_sync_enabled(self):
        """
        True if new products should be created during the sync
        """
        return self.get_boolean("periodic_sync_enabled", section=self.CISCO_EOX_CRAWLER_SECTION, default=False)

    def set_periodic_sync_enabled(self, value):
        """
        set the auto_create_new_products config value
        """
        if type(value) is not bool:
            raise ValueError("Value for the periodic_sync_enabled must be boolean")

        self._parser.set(option="periodic_sync_enabled", section=self.CISCO_EOX_CRAWLER_SECTION, value=str(value))

    def is_auto_create_new_products(self):
        """
        True if new products should be created during the sync
        """
        return self.get_boolean("auto_create_new_products", section=self.CISCO_EOX_CRAWLER_SECTION, default=False)

    def set_auto_create_new_products(self, value):
        """
        set the auto_create_new_products config value
        """
        if type(value) is not bool:
            raise ValueError("Value for the auto create new products must be boolean")

        self._parser.set(option="auto_create_new_products", section=self.CISCO_EOX_CRAWLER_SECTION, value=str(value))

    def get_cisco_eox_api_queries(self):
        """
        get Cisco EoX API queries
        """
        return self.get_string(key="eox_api_queries", section=self.CISCO_EOX_CRAWLER_SECTION, default="")

    def set_cisco_eox_api_queries(self, value):
        """
        set Cisco EoX API queries
        """
        self.set(key="eox_api_queries", section=self.CISCO_EOX_CRAWLER_SECTION, value=value)

    def get_product_blacklist_regex(self):
        """
        get Cisco EoX API queries
        """
        return self.get_string(key="product_blacklist_regex", section=self.CISCO_EOX_CRAWLER_SECTION, default="")

    def set_product_blacklist_regex(self, value):
        """
        set Cisco EoX API queries
        """
        self.set(key="product_blacklist_regex", section=self.CISCO_EOX_CRAWLER_SECTION, value=value)

    def get_cisco_api_client_id(self):
        """
        get Cisco API Client ID
        """
        return self.get_string(key="client_id", section=self.CISCO_API_SECTION, default="")

    def set_cisco_api_client_id(self, value):
        """
        set Cisco API Client ID
        """
        self.set(key="client_id", section=self.CISCO_API_SECTION, value=value)

    def get_cisco_api_client_secret(self):
        """
        get Cisco API Client secret
        """
        return self.get_string(key="client_secret", section=self.CISCO_API_SECTION, default="")

    def set_cisco_api_client_secret(self, value):
        """
        set Cisco API Client secret
        """
        self.set(key="client_secret", section=self.CISCO_API_SECTION, value=value)

    def get_cisco_eox_api_auto_sync_last_execution_time(self):
        """
        get the last execution time of the EoX API auto sync
        """
        return self.get_string(
            key="cisco_eox_api_auto_sync_last_execution_time",
            section=self.CISCO_EOX_CRAWLER_SECTION,
            default=""
        )

    def set_cisco_eox_api_auto_sync_last_execution_time(self, value):
        """
        set the last execution time value of the EoX API auto sync
        """
        self.set(
            key="cisco_eox_api_auto_sync_last_execution_time",
            section=self.CISCO_EOX_CRAWLER_SECTION,
            value=value
        )

    def get_cisco_eox_api_auto_sync_last_execution_result(self):
        """
        get the last execution result of the EoX API auto sync
        """
        return self.get_string(
            key="cisco_eox_api_auto_sync_last_execution_time",
            section=self.CISCO_EOX_CRAWLER_SECTION,
            default=""
        )

    def set_cisco_eox_api_auto_sync_last_execution_result(self, value):
        """
        set the last execution result of the EoX API auto sync
        """
        self.set(
            key="cisco_eox_api_auto_sync_last_execution_time",
            section=self.CISCO_EOX_CRAWLER_SECTION,
            value=value
        )

    def get_cisco_eox_api_auto_sync_enabled(self):
        """
        get the Cisco EoX API auto sync enabled state
        """
        return self.get_string(
            key="eox_api_auto_sync_enabled",
            section=self.CISCO_EOX_CRAWLER_SECTION,
            default=""
        )

    def set_cisco_eox_api_auto_sync_enabled(self, value):
        """
        set the Cisco EoX API auto sync enabled state
        """
        self.set(
            key="eox_api_auto_sync_enabled",
            section=self.CISCO_EOX_CRAWLER_SECTION,
            value=value
        )

    def get_cisco_api_credentials_last_message(self):
        """
        get the last message of the Cisco API access test
        """
        return self.get_string(
            key="cisco_api_credentials_last_message",
            section=self.CISCO_API_SECTION,
            default=""
        )

    def set_cisco_api_credentials_last_message(self, value):
        """
        set the last message of the Cisco API access test
        """
        self.set(
            key="cisco_api_credentials_last_message",
            section=self.CISCO_API_SECTION,
            value=value
        )

    def get_cisco_api_credentials_successful_tested(self):
        """
        get the last test state of the Cisco API access
        """
        return self.get_boolean(
            key="cisco_api_credentials_successful_tested",
            section=self.CISCO_API_SECTION,
            default=""
        )

    def set_cisco_api_credentials_successful_tested(self, value):
        """
        set the last test state of the Cisco API access
        """
        self.set(
            key="cisco_api_credentials_successful_tested",
            section=self.CISCO_API_SECTION,
            value=value
        )
