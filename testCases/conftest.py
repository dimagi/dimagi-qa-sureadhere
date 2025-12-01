import os
import base64
import pytest
import sys
from pathlib import Path
from seleniumbase import Driver
from seleniumbase import config as sb_config
from common_utilities.load_settings import load_settings
from common_utilities.path_settings import PathSettings
from selenium.webdriver.chrome.options import Options

# ---------------------
# Load environment settings
# ---------------------
@pytest.fixture(scope="session", autouse=True)
def settings():
    return load_settings()


@pytest.fixture
def rerun_count(request) -> int:
    exec_count = getattr(request.node, "execution_count", 1)  # 1 on first run
    return max(exec_count - 1, 0)  # 0 for first run, 1 for first rerun, etc.

@pytest.fixture(autouse=True)
def _inject_values(request, rerun_count):
    inst = getattr(request, "instance", None)
    if inst is not None:
        inst.rerun_count = rerun_count


@pytest.fixture(autouse=True)
def inject_settings_to_self(request, settings):
    if hasattr(request.node, "cls"):
        setattr(request.node.cls, "settings", settings)

# ---------------------
# Set SeleniumBase config
# ---------------------
@pytest.fixture(scope="session", autouse=True)
def configure_sb(settings):
    sb_config.settings.BROWSER = settings.get("browser", "chrome")
    sb_config.settings.WINDOW_SIZE = "1920,1080"
    sb_config.settings.WINDOW_POSITION = "0,0"
    sb_config.settings.DATA_DIR = str(PathSettings.DOWNLOAD_PATH)
    sb_config.settings.HEADLESS = settings.get("CI") == "true"
    sb_config.settings.START_PAGE = settings.get("url")
    sb_config.settings.IMPLICIT_WAIT = 10
    return sb_config.settings

# ---------------------
# Enable dashboard and report from PyCharm/CLI
# ---------------------
def pytest_configure(config):
    if not any(arg.startswith("--dashboard") for arg in sys.argv):
        config.option.dashboard = True
    if not config.option.htmlpath:
        config.option.htmlpath = "seleniumbase_report.html"
    if not config.option.self_contained_html:
        config.option.self_contained_html = True
# ---------------------
# Selenium WebDriver setup
# ---------------------
# @pytest.fixture(scope="function")
# def driver(settings):
#     driver = Driver(
#         browser=settings.get("browser", "chrome"),
#         headless=settings.get("CI") == "true"
#     )
#     driver.set_window_position(0, 0)
#     driver.set_window_size(1920, 1080)
#     driver.implicitly_wait(10)
#     yield driver
#     driver.quit()

# ---------------------
# Screenshot capture on failure (also adds to HTML report)
# ---------------------
def _capture_screenshot(driver):
    return base64.b64encode(driver.get_screenshot_as_png()).decode("utf-8")

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item):
    outcome = yield
    report = outcome.get_result()
    # NOTE: Only works if you are using BaseCase-based test class (self.driver)
    driver_instance = getattr(item.instance, "driver", None)

    if report.when in ("call", "teardown") and report.failed and driver_instance:
        screen_img = _capture_screenshot(driver_instance)
        html_content = (
            f'<div><img src="data:image/png;base64,{screen_img}" alt="screenshot" '
            f'style="width:600px;height:300px;" onclick="window.open(this.src)" align="right"/></div>'
        )
        extra = getattr(report, "extra", [])
        extra.append(item.config.pluginmanager.getplugin("html").extras.html(html_content))
        report.extra = extra

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    # Collect test counts
    passed = terminalreporter.stats.get('passed', [])
    failed = terminalreporter.stats.get('failed', [])
    error = terminalreporter.stats.get('error', [])
    skipped = terminalreporter.stats.get('skipped', [])
    xfail = terminalreporter.stats.get('xfail', [])

    env = os.environ.get("DIMAGIQA_ENV", "default_env")

    # Define the filename based on the environment
    filename = f'sa_test_counts_{env}.txt'

    # Write the counts to a file
    with open(filename, 'w') as f:
        f.write(f'PASSED={len(passed)}\n')
        f.write(f'FAILED={len(failed)}\n')
        f.write(f'ERROR={len(error)}\n')
        f.write(f'SKIPPED={len(skipped)}\n')
        f.write(f'XFAIL={len(xfail)}\n')

@pytest.fixture(scope="session", autouse=True)
def global_presetup_fixture():
    """Truly run once before any tests (even with xdist)."""
    print("\n>>> Running global presetup before all tests <<<")
    # Your setup logic here
    yield
    print("\n>>> Global presetup teardown after all tests <<<")


def pytest_collection_modifyitems(config, items):
    for item in items:
        # Skip if this test itself *defines* the presetup dependency root
        if any(
            m.name == "dependency" and m.kwargs.get("name") == "presetup"
            for m in item.own_markers
        ):
            continue

        # For everything else, make it depend on presetup
        item.add_marker(pytest.mark.dependency(depends=["presetup"]))


def pytest_runtest_setup(item):
    if item.get_closest_marker("run_on_main_process"):
        worker_id = getattr(item.config, "workerinput", {}).get("workerid", "master")
        if worker_id != "master":
            pytest.skip("Presetup runs only on master node")

@pytest.fixture(scope="function")
def driver(request, settings):
    """Create a normal or incognito driver depending on test marker."""
    is_incognito = request.node.get_closest_marker("incognito") is not None

    chrome_options = Options()
    if is_incognito:
        chrome_options.add_argument("--incognito")

    driver = Driver(
        browser=settings.get("browser", "chrome"),
        headless=settings.get("CI") == "true",
        chrome_options=chrome_options,
    )
    driver.set_window_position(0, 0)
    driver.set_window_size(1920, 1080)
    driver.set_script_timeout(60)
    driver.implicitly_wait(10)

    yield driver
    driver.quit()

@pytest.fixture(scope="function")
def two_drivers(driver, settings):
    """Reuse normal 'driver' + create an extra incognito one."""
    chrome_options = Options()
    chrome_options.add_argument("--incognito")

    incog = Driver(
        browser=settings.get("browser", "chrome"),
        headless=settings.get("CI") == "true",
        chrome_options=chrome_options,
    )
    incog.set_window_position(1300, 0)
    incog.set_window_size(1280, 900)
    incog.set_script_timeout(60)
    incog.implicitly_wait(10)

    try:
        yield driver, incog
    finally:
        incog.quit()
