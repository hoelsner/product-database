"""
py.test configuration file for the selenium test cases
"""
import os
import shutil
import pytest
import time
from selenium.webdriver import Firefox, DesiredCapabilities
from selenium.webdriver import FirefoxProfile

# directory which is used to download files during the selenium tests
DOWNLOAD_DIR = os.path.abspath(os.path.join("tests", "selenium_downloads"))
SELENIUM_TEST_CONFIG = "conf/product_database.test_selenium.config"

driver = None


@pytest.fixture(scope='session')
def browser(request):
    """
    initialize the selenium test case
    """
    global driver

    profile = FirefoxProfile()
    profile.accept_untrusted_certs = True
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", DOWNLOAD_DIR)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")

    capabilities = DesiredCapabilities.FIREFOX.copy()
    capabilities["acceptInsecureCerts"] = True

    driver = Firefox(firefox_profile=profile, capabilities=capabilities,
                     executable_path=os.getenv("FIREFOX_DRIVER_EXEC_PATH", "/usr/local/bin/geckodriver"))

    driver.implicitly_wait(10)
    driver.maximize_window()
    request.addfinalizer(lambda *args: driver.quit())

    yield driver

    time.sleep(5)


@pytest.fixture
def test_download_dir():
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    yield DOWNLOAD_DIR

    # clean download dir
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)


@pytest.fixture(scope="session", autouse=True)
def liveserver():
    server_host = os.environ.get("SERVER_HOST", "127.0.0.1")
    server_protocol = os.environ.get("SERVER_PROTOCOL", "https")
    server_port = os.environ.get("SERVER_PORT", "27443")

    return "%s://%s:%s" % (server_protocol, server_host, server_port)
