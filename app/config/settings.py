"""
Settings file class for the product database
"""
import logging
from app.config.models import ConfigOption

logger = logging.getLogger(__name__)


class AppSettings:
    """
    Product Database settings
    """
    def __init__(self):
        self.create_defaults()

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
        co, created = ConfigOption.objects.get_or_create(key=ConfigOption.GLOBAL_CISCO_API_ENABLED)
        if created:
            co.value = "false"
            co.save()

        co, created = ConfigOption.objects.get_or_create(key=ConfigOption.GLOBAL_LOGIN_ONLY_MODE)
        if created:
            co.value = "false"
            co.save()

        co, created = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_API_CLIENT_ID)
        if created:
            co.value = "PlsChgMe"
            co.save()

        co, created = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_API_CLIENT_SECRET)
        if created:
            co.value = "PlsChgMe"
            co.save()

        co, created = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_EOX_CRAWLER_AUTO_SYNC)
        if created:
            co.value = "false"
            co.save()

        co, created = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_EOX_CRAWLER_CREATE_PRODUCTS)
        if created:
            co.value = "false"
            co.save()

        co, created = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_EOX_API_QUERIES)
        if created:
            co.value = ""
            co.save()

        co, created = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_EOX_PRODUCT_BLACKLIST_REGEX)
        if created:
            co.value = ""
            co.save()

        co, created = ConfigOption.objects.get_or_create(key=ConfigOption.GLOBAL_INTERNAL_PRODUCT_ID_LABEL)
        if created:
            co.value = "Internal Product ID"
            co.save()

        co, created = ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_EOX_WAIT_TIME)
        if created:
            co.value = "5"
            co.save()

        ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_EOX_CRAWLER_LAST_EXECUTION_TIME)
        ConfigOption.objects.get_or_create(key=ConfigOption.CISCO_EOX_CRAWLER_LAST_EXECUTION_RESULT)

    def is_login_only_mode(self):
        """
        True if the login only mode is enabled in the configuration, otherwise False
        """
        co = ConfigOption.objects.get(key=ConfigOption.GLOBAL_LOGIN_ONLY_MODE)
        v = co.value.strip()

        return self._get_boolean(v)

    def set_login_only_mode(self, value):
        """
        enable/disable the login only mode
        """
        co = ConfigOption.objects.get(key=ConfigOption.GLOBAL_LOGIN_ONLY_MODE)
        self._set_boolean(co, value)

    def is_cisco_api_enabled(self):
        """
        True if the Cisco API is enabled in the configuration, otherwise False
        """
        co = ConfigOption.objects.get(key=ConfigOption.GLOBAL_CISCO_API_ENABLED)
        v = co.value.strip()

        return self._get_boolean(v)

    def set_cisco_api_enabled(self, value):
        """
        enable/disable the Cisco API access
        """
        co = ConfigOption.objects.get(key=ConfigOption.GLOBAL_CISCO_API_ENABLED)
        self._set_boolean(co, value)

    def is_periodic_sync_enabled(self):
        """
        True if new products should be created during the sync
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_EOX_CRAWLER_AUTO_SYNC)
        v = co.value.strip()

        return self._get_boolean(v)

    def set_periodic_sync_enabled(self, value):
        """
        set the auto_create_new_products config value
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_EOX_CRAWLER_AUTO_SYNC)
        self._set_boolean(co, value)

    def is_auto_create_new_products(self):
        """
        True if new products should be created during the sync
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_EOX_CRAWLER_CREATE_PRODUCTS)
        v = co.value.strip()

        return self._get_boolean(v)

    def set_auto_create_new_products(self, value):
        """
        set the auto_create_new_products config value
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_EOX_CRAWLER_CREATE_PRODUCTS)
        self._set_boolean(co, value)

    def get_cisco_eox_api_queries(self):
        """
        get Cisco EoX API queries
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_EOX_API_QUERIES)
        return co.value.strip()

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
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_EOX_API_QUERIES)
        co.value = value
        co.save()

    def get_product_blacklist_regex(self):
        """
        get Cisco EoX API queries
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_EOX_PRODUCT_BLACKLIST_REGEX)
        return co.value.strip()

    def set_product_blacklist_regex(self, value):
        """
        set Cisco EoX API queries
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_EOX_PRODUCT_BLACKLIST_REGEX)
        co.value = value
        co.save()

    def get_cisco_api_client_id(self):
        """
        get Cisco API Client ID
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_API_CLIENT_ID)
        return co.value.strip()

    def set_cisco_api_client_id(self, value):
        """
        set Cisco API Client ID
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_API_CLIENT_ID)
        co.value = value
        co.save()

    def get_cisco_api_client_secret(self):
        """
        get Cisco API Client secret
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_API_CLIENT_SECRET)
        return co.value.strip()

    def set_cisco_api_client_secret(self, value):
        """
        set Cisco API Client secret
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_API_CLIENT_SECRET)
        co.value = value
        co.save()

    def get_cisco_eox_api_auto_sync_last_execution_time(self):
        """
        get the last execution time of the EoX API auto sync
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_EOX_CRAWLER_LAST_EXECUTION_TIME)
        return co.value.strip()

    def set_cisco_eox_api_auto_sync_last_execution_time(self, value):
        """
        set the last execution time value of the EoX API auto sync
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_EOX_CRAWLER_LAST_EXECUTION_TIME)
        co.value = value
        co.save()

    def get_cisco_eox_api_auto_sync_last_execution_result(self):
        """
        get the last execution result of the EoX API auto sync
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_EOX_CRAWLER_LAST_EXECUTION_RESULT)
        return co.value

    def set_cisco_eox_api_auto_sync_last_execution_result(self, value):
        """
        set the last execution result of the EoX API auto sync
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_EOX_CRAWLER_LAST_EXECUTION_RESULT)
        co.value = value
        co.save()

    def get_internal_product_id_label(self):
        """
        get the custom label for the internal product ID
        """
        co = ConfigOption.objects.get(key=ConfigOption.GLOBAL_INTERNAL_PRODUCT_ID_LABEL)
        return co.value

    def set_internal_product_id_label(self, value):
        """
        set the custom label for the internal product ID
        """
        co = ConfigOption.objects.get(key=ConfigOption.GLOBAL_INTERNAL_PRODUCT_ID_LABEL)
        co.value = value
        co.save()

    def get_cisco_eox_api_sync_wait_time(self):
        """
        get the amount of seconds to wait between each API call
        :return:
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_EOX_WAIT_TIME)
        return co.value

    def set_cisco_eox_api_sync_wait_time(self, value):
        """
        set the Cisco EoX API timeout
        :param value:
        :return:
        """
        co = ConfigOption.objects.get(key=ConfigOption.CISCO_EOX_WAIT_TIME)
        co.value = value
        co.save()
