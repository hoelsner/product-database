"""
py.test configuration file for the selenium test cases
"""
import os
import json
import shutil
import pytest
import requests
import time
from requests.auth import HTTPBasicAuth
from selenium.webdriver import Firefox
from selenium.webdriver import FirefoxProfile
from app.config import utils
from tests import PRODUCT_GROUPS_API_ENDPOINT, PRODUCTS_API_ENDPOINT

pytestmark = pytest.mark.django_db

# directory which is used to download files during the selenium tests
DOWNLOAD_DIR = os.path.abspath(os.path.join("tests", "selenium_downloads"))
SELENIUM_TEST_CONFIG = "conf/product_database.test_selenium.config"


browsers = {
    'firefox': Firefox
}


@pytest.fixture(scope='session')
def browser(request):
    """
    initialize the selenium test case
    """
    profile = FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", DOWNLOAD_DIR)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")

    b = Firefox(firefox_profile=profile)
    b.implicitly_wait(10)
    b.maximize_window()
    request.addfinalizer(lambda *args: b.quit())
    yield b
    time.sleep(10)


@pytest.fixture
def set_test_config_file(settings):
    """Set a different configuration file, that is removed after the execution"""
    settings.APP_CONFIG_FILE = SELENIUM_TEST_CONFIG
    yield

    # cleanup the configuration after the execution
    if os.path.exists(SELENIUM_TEST_CONFIG):
        os.remove(SELENIUM_TEST_CONFIG)


@pytest.fixture
def mock_cisco_eox_api_access_available(monkeypatch):
    monkeypatch.setattr(utils, "check_cisco_eox_api_access",
                        lambda client_id, client_secret, drop_credentials=False: True)


@pytest.fixture
def test_download_dir():
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    yield DOWNLOAD_DIR

    # clean download dir
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)


@pytest.fixture
@pytest.mark.usefixtures("import_default_users")
@pytest.mark.usefixtures("import_default_vendors")
def base_data_for_test_case(live_server):
    files = [
        os.path.join("tests", "data", "cisco_test_data.json"),
        os.path.join("tests", "data", "juniper_test_data.json")
    ]
    vendors = {
        "Cisco Systems": 1,
        "Juniper Networks": 2
    }
    productgroup_ids = {}
    for file in files:
        with open(file) as f:
            jdata = json.loads(f.read())

        productgroups = jdata["product_groups"]
        products = jdata["products"]

        for productgroup in productgroups:
            productgroup['vendor'] = vendors[productgroup['vendor']]
            response = requests.post(live_server + PRODUCT_GROUPS_API_ENDPOINT,
                                     auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                     data=json.dumps(productgroup),
                                     headers={'Content-Type': 'application/json'},
                                     verify=False,
                                     timeout=10)
            assert response.ok is True
            productgroup_ids[response.json()["name"]] = response.json()["id"]

        for product in products:
            product['vendor'] = vendors[product['vendor']]
            if "product_group" in product:
                product['product_group'] = productgroup_ids[product['product_group']]
            response = requests.post(live_server + PRODUCTS_API_ENDPOINT,
                                     auth=HTTPBasicAuth("pdb_admin", "pdb_admin"),
                                     data=json.dumps(product),
                                     headers={'Content-Type': 'application/json'},
                                     verify=False,
                                     timeout=10)
            assert response.ok is True
