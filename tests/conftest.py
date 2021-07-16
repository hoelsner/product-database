"""
py.test configuration file for the selenium test cases
"""
import os
import shutil
import pytest
import time
from selenium.webdriver import Firefox, FirefoxProfile, DesiredCapabilities
from selenium.webdriver.firefox.options import Options
from pyvirtualdisplay import Display

# directory which is used to download files during the selenium tests
DOWNLOAD_DIR = os.path.abspath(os.path.join("tests", "selenium_downloads"))
SELENIUM_TEST_CONFIG = "conf/product_database.test_selenium.config"

driver = None


def _capture_screenshot(name):
    if driver is not None:
        driver.get_screenshot_as_file(name)


@pytest.fixture(scope="session", autouse=True)
def screenshotter():
    def shot(name):
        return _capture_screenshot("screenshotter--%s" % name)

    return shot


@pytest.mark.hookwrapper
def pytest_runtest_makereport(item):
    """
    Extends the PyTest Plugin to take and embed screenshot in html report, whenever a test fails.
    :param item:
    """
    pytest_html = item.config.pluginmanager.getplugin('html')
    outcome = yield
    report = outcome.get_result()
    extra = getattr(report, 'extra', [])

    if report.when == 'call' or report.when == "setup":
        xfail = hasattr(report, 'wasxfail')
        if (report.skipped and xfail) or (report.failed and not xfail):
            file_name = report.nodeid.replace("::", "_").replace("/", "_") + ".png"
            print(f">>>>>>>>>>>>> screenshot saved to {os.path.join('coverage_report', file_name)}")
            _capture_screenshot(os.path.join("coverage_report", file_name))
            if file_name:
                html = '<div><img src="%s" alt="screenshot" style="width:304px;height:228px;" ' \
                       'onclick="window.open(this.src)" align="right"/></div>' % file_name
                extra.append(pytest_html.extras.html(html))

        report.extra = extra


@pytest.fixture(scope='session')
def browser(request):
    """
    initialize the selenium test case
    """
    global driver

    headless_testing = os.environ.get("HEADLESS_TESTING", False)

    profile = FirefoxProfile()
    profile.accept_untrusted_certs = True
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", DOWNLOAD_DIR)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")

    capabilities = DesiredCapabilities.FIREFOX.copy()
    capabilities["acceptInsecureCerts"] = True

    opts = Options()
    opts.log.level = "trace"

    if headless_testing:
        display = Display(visible=0, size=(1920, 1080))
        display.start()
        time.sleep(3)

        driver = Firefox(
            firefox_profile=profile,
            options=opts,
            capabilities=capabilities,
            executable_path=os.getenv("FIREFOX_DRIVER_EXEC_PATH", "/usr/local/bin/geckodriver")
        )
        driver.set_window_size(1654, 859)

    else:
        driver = Firefox(
            firefox_profile=profile,
            options=opts,
            capabilities=capabilities,
            executable_path=os.getenv("FIREFOX_DRIVER_EXEC_PATH", "/usr/local/bin/geckodriver")
        )
        driver.maximize_window()

    driver.implicitly_wait(20)
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
    # pytest will stage the docker-compose_test.yaml file that uses port 27443 on the device
    server_port = os.environ.get("SERVER_PORT", "27443")

    return "%s://%s:%s" % (server_protocol, server_host, server_port)
