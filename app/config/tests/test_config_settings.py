"""
Test suite for the config.settings module
"""
import pytest
import os
import json
from datetime import datetime
from django.utils.dateparse import parse_datetime
from app.config import AppSettings
from app.config.tests import CONFIG_FILE_PATH


@pytest.mark.usefixtures("set_test_app_config_file_setting")
class TestConfigSettingsMigrated:
    def clean_config_file(self):
        # cleanup
        if os.path.exists(CONFIG_FILE_PATH):
            os.remove(CONFIG_FILE_PATH)

    def test_create_default_config(self):
        self.clean_config_file()

        # create new AppSettings object and create defaults
        settings = AppSettings()
        settings.create_defaults()

        # verify result
        assert os.path.exists(CONFIG_FILE_PATH) is True

        # test dictionary (booleans are converted as string)
        assert json.dumps(settings.CONFIG_DEFAULTS, sort_keys=True) == \
               json.dumps(settings.to_dictionary(), sort_keys=True)

        # cleanup
        self.clean_config_file()

    def test_read_with_missing_file(self):
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        assert os.path.exists(CONFIG_FILE_PATH) is False

        # read file specified in the settings
        settings.read_file()
        assert os.path.exists(CONFIG_FILE_PATH) is True

        # cleanup
        self.clean_config_file()

    def test_get_cisco_eox_queries_from_config(self):
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        assert os.path.exists(CONFIG_FILE_PATH) is False
        settings.read_file()
        assert os.path.exists(CONFIG_FILE_PATH) is True

        # get values
        value = settings.get_cisco_eox_api_queries()
        assert value == ""

        # set values
        queries = "test"
        settings.set_cisco_eox_api_queries(queries)
        settings.write_file()
        value = settings.get_cisco_eox_api_queries()

        assert value == queries

        # cleanup
        self.clean_config_file()

    def test_get_product_blacklist_regex_from_config(self):
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        assert os.path.exists(CONFIG_FILE_PATH) is False
        settings.read_file()
        assert os.path.exists(CONFIG_FILE_PATH) is True

        # get values
        value = settings.get_product_blacklist_regex()
        assert value == ""

        # set values
        blacklist_entries = "test\nanother\ntest"
        settings.set_product_blacklist_regex(blacklist_entries)
        settings.write_file()
        value = settings.get_product_blacklist_regex()

        assert value == blacklist_entries

        # cleanup
        self.clean_config_file()

    def test_get_cisco_api_client_id(self):
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        assert os.path.exists(CONFIG_FILE_PATH) is False
        settings.read_file()
        assert os.path.exists(CONFIG_FILE_PATH) is True

        # get values
        value = settings.get_cisco_api_client_id()
        assert value == "PlsChgMe"

        # set values
        value = "test_id"
        settings.set_cisco_api_client_id(value)
        settings.write_file()
        value = settings.get_cisco_api_client_id()

        assert value == value

        # cleanup
        self.clean_config_file()

    def test_get_cisco_api_client_secret(self):
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        assert os.path.exists(CONFIG_FILE_PATH) is False
        settings.read_file()
        assert os.path.exists(CONFIG_FILE_PATH) is True

        # get values
        value = settings.get_cisco_api_client_secret()
        assert value == "PlsChgMe"

        # set values
        value = "test_secret"
        settings.set_cisco_api_client_secret(value)
        settings.write_file()
        value = settings.get_cisco_api_client_secret()

        assert value == value

        # cleanup
        self.clean_config_file()

    def test_auto_create_new_products(self):
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        assert os.path.exists(CONFIG_FILE_PATH) is False
        settings.read_file()
        assert os.path.exists(CONFIG_FILE_PATH) is True

        # get values
        value = settings.is_auto_create_new_products()
        assert value == False

        # set values
        settings.set_auto_create_new_products(True)
        settings.write_file()
        value = settings.is_auto_create_new_products()

        assert value == True

        # cleanup
        self.clean_config_file()

    def test_get_config_value(self):
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        settings.create_defaults()

        # get a configuration value (default in the global section)
        assert settings.get_boolean("cisco_api_enabled") is False

        # get a configuration value (with an explicit option)
        assert "PlsChgMe" == settings.get_string("client_id", section=AppSettings.CISCO_API_SECTION)

        # get the default Cisco API enabled value
        assert settings.is_cisco_api_enabled() is False

        # set a new value
        settings.set_cisco_api_enabled(True)

        # set an invalid value
        with pytest.raises(ValueError):
            settings.set_cisco_api_enabled("invalid value")

        # write results
        settings.write_file()

        # cleanup
        self.clean_config_file()

    def test_write_datetime_to_settings_file(self):
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        settings.create_defaults()

        # get a configuration value (default in the global section)
        now = datetime.now()
        value = now.isoformat()
        settings.set(
            key="cisco_eox_api_auto_sync_last_execution_time",
            section=AppSettings.CISCO_EOX_CRAWLER_SECTION,
            value=value
        )

        settings.write_file()

        read_value = settings.get_string(
            key="cisco_eox_api_auto_sync_last_execution_time",
            section=AppSettings.CISCO_EOX_CRAWLER_SECTION
        )
        assert value == read_value
        assert now == parse_datetime(read_value)

        # cleanup
        self.clean_config_file()

