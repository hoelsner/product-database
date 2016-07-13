import json
import os

from django.test import TestCase
from django.test import override_settings
from django.utils.timezone import datetime
from django.utils.dateparse import parse_datetime

from app.config import AppSettings


@override_settings(APP_CONFIG_FILE="conf/product_database.defaults.config")
class ConfigFileSettingsTest(TestCase):
    """
    Test the config file settings class
    """
    TEST_CONFIG_FILE = "conf/product_database.defaults.config"

    def clean_config_file(self):
        # cleanup
        if os.path.exists(self.TEST_CONFIG_FILE):
            os.remove(self.TEST_CONFIG_FILE)

    def test_create_default_config(self):
        """
        test the create of the default configuration
        """
        self.clean_config_file()

        # create new AppSettings object and create defaults
        settings = AppSettings()
        settings.create_defaults()

        # verify result
        self.assertTrue(os.path.exists(self.TEST_CONFIG_FILE))

        # test dictionary (booleans are converted as string)
        self.assertEqual(
            json.dumps(settings.CONFIG_DEFAULTS, sort_keys=True),
            json.dumps(settings.to_dictionary(), sort_keys=True)
        )

        # cleanup
        self.clean_config_file()

    def test_read_with_missing_file(self):
        """
        test the read function if no file exists
        """
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        self.assertFalse(os.path.exists(self.TEST_CONFIG_FILE))

        # read file specified in the settings
        settings.read_file()
        self.assertTrue(os.path.exists(self.TEST_CONFIG_FILE))

        # cleanup
        self.clean_config_file()

    def test_get_cisco_eox_queries_from_config(self):
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        self.assertFalse(os.path.exists(self.TEST_CONFIG_FILE))
        settings.read_file()
        self.assertTrue(os.path.exists(self.TEST_CONFIG_FILE))

        # get values
        value = settings.get_cisco_eox_api_queries()
        self.assertEqual(value, "")

        # set values
        queries = "test"
        settings.set_cisco_eox_api_queries(queries)
        settings.write_file()
        value = settings.get_cisco_eox_api_queries()

        self.assertEqual(value, queries)

        # cleanup
        self.clean_config_file()

    def test_get_product_blacklist_regex_from_config(self):
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        self.assertFalse(os.path.exists(self.TEST_CONFIG_FILE))
        settings.read_file()
        self.assertTrue(os.path.exists(self.TEST_CONFIG_FILE))

        # get values
        value = settings.get_product_blacklist_regex()
        self.assertEqual(value, "")

        # set values
        blacklist_entries = "test\nanother\ntest"
        settings.set_product_blacklist_regex(blacklist_entries)
        settings.write_file()
        value = settings.get_product_blacklist_regex()

        self.assertEqual(value, blacklist_entries)

        # cleanup
        self.clean_config_file()

    def test_get_cisco_api_client_id(self):
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        self.assertFalse(os.path.exists(self.TEST_CONFIG_FILE))
        settings.read_file()
        self.assertTrue(os.path.exists(self.TEST_CONFIG_FILE))

        # get values
        value = settings.get_cisco_api_client_id()
        self.assertEqual(value, "PlsChgMe")

        # set values
        value = "test_id"
        settings.set_cisco_api_client_id(value)
        settings.write_file()
        value = settings.get_cisco_api_client_id()

        self.assertEqual(value, value)

        # cleanup
        self.clean_config_file()

    def test_get_cisco_api_client_secret(self):
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        self.assertFalse(os.path.exists(self.TEST_CONFIG_FILE))
        settings.read_file()
        self.assertTrue(os.path.exists(self.TEST_CONFIG_FILE))

        # get values
        value = settings.get_cisco_api_client_secret()
        self.assertEqual(value, "PlsChgMe")

        # set values
        value = "test_secret"
        settings.set_cisco_api_client_secret(value)
        settings.write_file()
        value = settings.get_cisco_api_client_secret()

        self.assertEqual(value, value)

        # cleanup
        self.clean_config_file()

    def test_auto_create_new_products(self):
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        self.assertFalse(os.path.exists(self.TEST_CONFIG_FILE))
        settings.read_file()
        self.assertTrue(os.path.exists(self.TEST_CONFIG_FILE))

        # get values
        value = settings.is_auto_create_new_products()
        self.assertEqual(value, False)

        # set values
        settings.set_auto_create_new_products(True)
        settings.write_file()
        value = settings.is_auto_create_new_products()

        self.assertEqual(value, True)

        # cleanup
        self.clean_config_file()

    def test_get_config_value(self):
        self.clean_config_file()

        # create new AppSettings object
        settings = AppSettings()
        settings.create_defaults()

        # get a configuration value (default in the global section)
        self.assertFalse(settings.get_boolean("cisco_api_enabled"))

        # get a configuration value (with an explicit option)
        self.assertEqual("PlsChgMe", settings.get_string("client_id", section=AppSettings.CISCO_API_SECTION))

        # get the default Cisco API enabled value
        self.assertFalse(settings.is_cisco_api_enabled())

        # set a new value
        settings.set_cisco_api_enabled(True)

        # set an invalid value
        with self.assertRaises(ValueError):
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
        self.assertEqual(value, read_value)
        self.assertEqual(now, parse_datetime(read_value))

        # cleanup
        self.clean_config_file()
