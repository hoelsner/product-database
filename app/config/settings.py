"""
Settings file class for the product database
"""
import logging
from app.config.models import ConfigOption
from django.core.cache import cache

logger = logging.getLogger(__name__)


class AppSettings:
    """
    Product Database settings
    """
    CONFIG_OPTIONS_DICT_CACHE_KEY = "PRODUCTDB_CONFIG_OPTIONS"

    def __init__(self):
        self._config_options = cache.get(self.CONFIG_OPTIONS_DICT_CACHE_KEY, None)
        if not self._config_options or len(self._config_options) < 12:
            # populate cache
            self.create_defaults()
            self._config_options = dict(ConfigOption.objects.all().values_list("key", "value"))
            cache.set(self.CONFIG_OPTIONS_DICT_CACHE_KEY, self._config_options, timeout=None)

    def _rebuild_config_cache(self):
        cache.delete(self.CONFIG_OPTIONS_DICT_CACHE_KEY)
        self._config_options = dict(ConfigOption.objects.all().values_list("key", "value"))
        cache.set(self.CONFIG_OPTIONS_DICT_CACHE_KEY, self._config_options, timeout=None)

    def _set_boolean(self, config_object, value):
        if value:
            config_object.value = "true"

        else:
            config_object.value = "false"

        config_object.save()

    def _get_boolean(self, value):
        result = True
        if value:
            if value == "0" or value == "false" or value == "":
                result = False

        return result

    @staticmethod
    def create_defaults():
        """
        create default configuration if not set
        """
        expected_defaults = {
            ConfigOption.GLOBAL_CISCO_API_ENABLED: "false",
            ConfigOption.GLOBAL_LOGIN_ONLY_MODE: "false",
            ConfigOption.CISCO_API_CLIENT_ID: "PlsChgMe",
            ConfigOption.CISCO_API_CLIENT_SECRET: "PlsChgMe",
            ConfigOption.CISCO_EOX_CRAWLER_AUTO_SYNC: "false",
            ConfigOption.CISCO_EOX_CRAWLER_CREATE_PRODUCTS: "false",
            ConfigOption.CISCO_EOX_API_QUERIES: "",
            ConfigOption.CISCO_EOX_PRODUCT_BLACKLIST_REGEX: "",
            ConfigOption.GLOBAL_INTERNAL_PRODUCT_ID_LABEL: "Internal Product ID",
            ConfigOption.CISCO_EOX_WAIT_TIME: "5",
            ConfigOption.CISCO_EOX_CRAWLER_LAST_EXECUTION_TIME: None,
            ConfigOption.CISCO_EOX_CRAWLER_LAST_EXECUTION_RESULT: None,
            ConfigOption.STAT_AMOUNT_OF_PRODUCT_CHECKS: "0",
            ConfigOption.STAT_AMOUNT_OF_UNIQUE_PRODUCT_CHECK_ENTRIES: "0"
        }
        for key, value in expected_defaults.items():
            if not ConfigOption.objects.filter(key=key).exists():
                co = ConfigOption.objects.create(key=key)
                co.value = value
                co.save()

    def is_login_only_mode(self):
        """
        True if the login only mode is enabled in the configuration, otherwise False
        """
        return self._get_boolean(self._config_options[ConfigOption.GLOBAL_LOGIN_ONLY_MODE])

    def set_login_only_mode(self, value):
        """
        enable/disable the login only mode
        """
        co, created = ConfigOption.objects.get_or_create(key=ConfigOption.GLOBAL_LOGIN_ONLY_MODE)
        self._set_boolean(co, value)
        self._rebuild_config_cache()

    def is_cisco_api_enabled(self):
        """
        True if the Cisco API is enabled in the configuration, otherwise False
        """
        return self._get_boolean(self._config_options[ConfigOption.GLOBAL_CISCO_API_ENABLED])

    def set_cisco_api_enabled(self, value):
        """
        enable/disable the Cisco API access
        """
        co, _ = ConfigOption.objects.get_or_create(key=ConfigOption.GLOBAL_CISCO_API_ENABLED)
        self._set_boolean(co, value)
        self._rebuild_config_cache()

    def is_periodic_sync_enabled(self):
        """
        True if new products should be created during the sync
        """
        return self._get_boolean(self._config_options[ConfigOption.CISCO_EOX_CRAWLER_AUTO_SYNC])

    def set_periodic_sync_enabled(self, value):
        """
        set the auto_create_new_products config value
        """
        co, _ = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_EOX_CRAWLER_AUTO_SYNC)
        self._set_boolean(co, value)
        self._rebuild_config_cache()

    def is_auto_create_new_products(self):
        """
        True if new products should be created during the sync
        """
        return self._get_boolean(self._config_options[ConfigOption.CISCO_EOX_CRAWLER_CREATE_PRODUCTS])

    def set_auto_create_new_products(self, value):
        """
        set the auto_create_new_products config value
        """
        co, _ = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_EOX_CRAWLER_CREATE_PRODUCTS)
        self._set_boolean(co, value)
        self._rebuild_config_cache()

    def get_cisco_eox_api_queries(self):
        """
        get Cisco EoX API queries
        """
        return self._config_options[ConfigOption.CISCO_EOX_API_QUERIES]\
            if self._config_options[ConfigOption.CISCO_EOX_API_QUERIES] else ""

    def get_cisco_eox_api_queries_as_list(self):
        """
        clean queries string and remove empty statements
        (split lines, if any and split the string by semicolon)
        """
        queries = []
        for e in [e.split(";") for e in self.get_cisco_eox_api_queries().splitlines()]:
            queries += e
        return [e for e in queries if e != ""]

    def set_cisco_eox_api_queries(self, value):
        """
        set Cisco EoX API queries
        """
        co, _ = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_EOX_API_QUERIES)
        co.value = value
        co.save()
        self._rebuild_config_cache()

    def get_product_blacklist_regex(self):
        """
        get Cisco EoX API queries
        """
        return self._config_options[ConfigOption.CISCO_EOX_PRODUCT_BLACKLIST_REGEX]\
            if self._config_options[ConfigOption.CISCO_EOX_PRODUCT_BLACKLIST_REGEX] else ""

    def set_product_blacklist_regex(self, value):
        """
        set Cisco EoX API queries
        """
        co, _ = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_EOX_PRODUCT_BLACKLIST_REGEX)
        co.value = value
        co.save()
        self._rebuild_config_cache()

    def get_cisco_api_client_id(self):
        """
        get Cisco API Client ID
        """
        return self._config_options[ConfigOption.CISCO_API_CLIENT_ID]

    def set_cisco_api_client_id(self, value):
        """
        set Cisco API Client ID
        """
        co, _ = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_API_CLIENT_ID)
        co.value = value
        co.save()
        self._rebuild_config_cache()

    def get_cisco_api_client_secret(self):
        """
        get Cisco API Client secret
        """
        return self._config_options[ConfigOption.CISCO_API_CLIENT_SECRET]

    def set_cisco_api_client_secret(self, value):
        """
        set Cisco API Client secret
        """
        co, _ = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_API_CLIENT_SECRET)
        co.value = value
        co.save()
        self._rebuild_config_cache()

    def get_cisco_eox_api_auto_sync_last_execution_time(self):
        """
        get the last execution time of the EoX API auto sync
        """
        return self._config_options[ConfigOption.CISCO_EOX_CRAWLER_LAST_EXECUTION_TIME]

    def set_cisco_eox_api_auto_sync_last_execution_time(self, value):
        """
        set the last execution time value of the EoX API auto sync
        """
        co, _ = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_EOX_CRAWLER_LAST_EXECUTION_TIME)
        co.value = value
        co.save()
        self._rebuild_config_cache()

    def get_cisco_eox_api_auto_sync_last_execution_result(self):
        """
        get the last execution result of the EoX API auto sync
        """
        return self._config_options[ConfigOption.CISCO_EOX_CRAWLER_LAST_EXECUTION_RESULT]

    def set_cisco_eox_api_auto_sync_last_execution_result(self, value):
        """
        set the last execution result of the EoX API auto sync
        """
        co, _ = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_EOX_CRAWLER_LAST_EXECUTION_RESULT)
        co.value = value
        co.save()
        self._rebuild_config_cache()

    def get_internal_product_id_label(self):
        """
        get the custom label for the internal product ID
        """
        return self._config_options[ConfigOption.GLOBAL_INTERNAL_PRODUCT_ID_LABEL]

    def set_internal_product_id_label(self, value):
        """
        set the custom label for the internal product ID
        """
        co, _ = ConfigOption.objects.get_or_create(key=ConfigOption.GLOBAL_INTERNAL_PRODUCT_ID_LABEL)
        co.value = value
        co.save()
        self._rebuild_config_cache()

    def get_cisco_eox_api_sync_wait_time(self):
        """
        get the amount of seconds to wait between each API call
        :return:
        """
        return self._config_options[ConfigOption.CISCO_EOX_WAIT_TIME]

    def set_cisco_eox_api_sync_wait_time(self, value):
        """
        set the Cisco EoX API timeout
        :param value:
        :return:
        """
        co, _ = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_EOX_WAIT_TIME)
        co.value = value
        co.save()
        self._rebuild_config_cache()

    def set_amount_of_product_checks(self, value):
        """
        set amount of product checks statistics counter
        """
        co, created = ConfigOption.objects.get_or_create(key=ConfigOption.STAT_AMOUNT_OF_PRODUCT_CHECKS)
        co.value = str(int(value))
        co.save()
        self._rebuild_config_cache()

    def get_amount_of_product_checks(self):
        """
        get amount of product checks statistics counter
        :return:
        """
        try:
            return int(self._config_options[ConfigOption.STAT_AMOUNT_OF_PRODUCT_CHECKS])\
                if self._config_options[ConfigOption.STAT_AMOUNT_OF_PRODUCT_CHECKS] else 0
        except:  # catch any exception
            # may occur after update, after cleaning the cache value it should work
            cache.delete(self.CONFIG_OPTIONS_DICT_CACHE_KEY)
            return -1

    def set_amount_of_unique_product_check_entries(self, value):
        """
        set amount of unique product check entries statistics counter
        """
        co, created = ConfigOption.objects.get_or_create(key=ConfigOption.STAT_AMOUNT_OF_UNIQUE_PRODUCT_CHECK_ENTRIES)
        co.value = str(int(value))
        co.save()
        self._rebuild_config_cache()

    def get_amount_of_unique_product_check_entries(self):
        """
        get amount of unique product check entries statistics counter
        :return:
        """
        try:
            return int(self._config_options[ConfigOption.STAT_AMOUNT_OF_UNIQUE_PRODUCT_CHECK_ENTRIES])\
                if self._config_options[ConfigOption.STAT_AMOUNT_OF_UNIQUE_PRODUCT_CHECK_ENTRIES] else 0
        except:  # catch any exception
            # may occur after update, after cleaning the cache value it should work
            cache.delete(self.CONFIG_OPTIONS_DICT_CACHE_KEY)
            return -1
