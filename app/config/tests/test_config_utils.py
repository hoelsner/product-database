"""
Test suite for the config.utils module
"""
import pytest
from app.ciscoeox.base_api import CiscoEoxApi
from app.config.utils import check_cisco_hello_api_access, check_cisco_eox_api_access

pytestmark = pytest.mark.django_db
online = pytest.mark.skipif(not pytest.config.getoption("--online"), reason="need --online to run")


@pytest.mark.usefixtures("import_default_vendors")
@online
class TestConfigUtils:
    def test_cisco_hello_api_access(self):
        eox_call = CiscoEoxApi()
        eox_call.load_client_credentials()

        assert check_cisco_hello_api_access(eox_call.client_id, eox_call.client_secret, drop_credentials=False) is True

    def test_cisco_eox_api_access(self):
        eox_call = CiscoEoxApi()
        eox_call.load_client_credentials()

        assert check_cisco_eox_api_access(eox_call.client_id, eox_call.client_secret, drop_credentials=False) is True
