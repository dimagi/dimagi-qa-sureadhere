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
import matplotlib.pyplot as plt
from PIL import Image

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


def _relogin(inst):
    """Re-establish a logged-in session on test reruns.

    If the browser is already on the login page, login directly.
    Otherwise logout first, then login.
    Falls back to a fresh URL load if either path raises an exception.
    """
    from testPages.login_page.login_page import LoginPage
    from testPages.home_page.home_page import HomePage
    from testPages.user_profile.user_profile_page import UserProfilePage

    login = LoginPage(inst, "login")
    home = HomePage(inst, "dashboard")
    settings = inst.settings

    try:
        if login.is_element_visible("next"):
            print("[rerun] Already on login page — logging in directly")
            login.login(settings["login_username"], settings["login_password"])
        else:
            print("[rerun] Not on login page — logging out first, then logging in")
            home.click_admin_profile_button()
            profile = UserProfilePage(inst, "user")
            profile.logout_user()
            login.after_logout()
            login.login(settings["login_username"], settings["login_password"])
        home.validate_dashboard_page()
    except Exception as e:
        print(f"[rerun] Re-login via current page failed ({e}), retrying via URL...")
        login.launch_browser(settings["url"])
        login.login(settings["login_username"], settings["login_password"])
        home.validate_dashboard_page()


@pytest.fixture(autouse=True)
def _relogin_on_rerun(request, rerun_count):
    inst = getattr(request, "instance", None)
    if inst is None or rerun_count == 0:
        yield
        return

    # Autouse fixtures run before BaseCase.setUp() initializes the driver, so
    # calling SeleniumBase methods here would raise OutOfScopeException.
    # Instead, wrap setUp() so the relogin runs immediately after the driver
    # is ready.
    original_setUp = inst.setUp

    def patched_setUp():
        original_setUp()
        _relogin(inst)

    inst.setUp = patched_setUp
    yield


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

    # 👇 Remove noisy logs
    sb_config.settings.VERBOSE = False
    sb_config.settings.PRINT_STEP_TIMING = False
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
    if not driver:
        return None
    try:
        png = driver.get_screenshot_as_png()
        if not png:
            return None
        return base64.b64encode(png).decode("utf-8")
    except Exception as e:
        print(f"[WARN] Screenshot capture failed: {e}")
        return None

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item):
    pytest_html = item.config.pluginmanager.getplugin("html")

    outcome = yield
    report = outcome.get_result()
    # NOTE: Only works if you are using BaseCase-based test class (self.driver)
    driver_instance = getattr(item.instance, "driver", None)
    # -------------------------
    # Add Google Sheet Link
    # -------------------------
    testcase_marker = item.get_closest_marker("testcase")
    tcid_marker = item.get_closest_marker("tcid")

    if testcase_marker and tcid_marker:
        tcid = tcid_marker.args[0]
        link = testcase_marker.args[0]
        link_html = (
            f'<div style="margin-bottom:8px;">'
            f'<span style="margin-right:4px;">📄 Link to testcase:</span>'
            f'<a href="{link}" target="_blank" '
            f'style="font-weight:600;color:#1a73e8;text-decoration:none;">'
            f'{tcid}</a>'
            f'</div>'
        )
        extra = getattr(report, "extra", [])
        if pytest_html:
            extra.append(pytest_html.extras.html(link_html))
            report.extra = extra

    if report.when in ("call", "teardown") and report.failed:
        extra = getattr(report, "extra", [])

        if driver_instance:
            screen_img = _capture_screenshot(driver_instance)
            if screen_img and pytest_html:
                extra.append(pytest_html.extras.image(screen_img, "Web Screenshot"))

        mobile_instance = getattr(item.instance, "mobile", None)
        mobile_driver = getattr(mobile_instance, "driver", None) if mobile_instance else None
        if mobile_driver:
            mob_img = _capture_screenshot(mobile_driver)
            if mob_img and pytest_html:
                extra.append(pytest_html.extras.image(mob_img, "Mobile Screenshot"))

        if extra != getattr(report, "extra", []):
            report.extra = extra

def save_summary_charts(stats):
    out_dir = Path("slack_charts")
    out_dir.mkdir(exist_ok=True)

    passed  = stats.get("passed", 0)
    failed  = stats.get("failed", 0)
    skipped = stats.get("skipped", 0)
    reruns  = stats.get("reruns", 0)

    # Pie / donut chart
    fig, ax = plt.subplots()
    ax.pie(
        [passed, failed, skipped],
        labels=None,
        colors=["#66bb6a", "#ef5350", "#fad000"],
        startangle=90,
        wedgeprops=dict(width=0.4),
    )
    ax.axis("equal")
    ax.set_title("Test Summary")
    ax.legend(
        [f"Passed: {passed}", f"Failed: {failed}", f"Skipped: {skipped}"],
        loc="lower center",
        ncol=3,
        bbox_to_anchor=(0.5, -0.15),
    )
    fig.savefig(out_dir / "summary_pie.png", bbox_inches="tight")
    plt.close(fig)

    # Bar chart (only when there are failures or reruns)
    bar_path = None
    if failed > 0 or reruns > 0:
        fig, ax = plt.subplots()
        bars = ax.bar(["Failed", "Reruns"], [failed, reruns], color=["#ef5350", "#ffa726"])
        ax.set_ylabel("Number of Tests")
        ax.set_title("Failures and Reruns")
        ax.legend(
            [bars[0], bars[1]],
            [f"Failed: {failed}", f"Reruns: {reruns}"],
            loc="lower center",
            ncol=2,
            bbox_to_anchor=(0.5, -0.15),
        )
        bar_path = out_dir / "summary_bar.png"
        fig.savefig(bar_path, bbox_inches="tight")
        plt.close(fig)

    _combine_charts(
        pie_path=out_dir / "summary_pie.png",
        bar_path=bar_path,
        combined_path=out_dir / "summary_combined.png",
    )


def _combine_charts(pie_path, bar_path, combined_path):
    pie = Image.open(pie_path)
    if bar_path and Path(bar_path).exists():
        bar = Image.open(bar_path)
        bar = bar.resize((bar.width * pie.height // bar.height, pie.height))
        combined = Image.new("RGB", (pie.width + bar.width, pie.height), (255, 255, 255))
        combined.paste(pie, (0, 0))
        combined.paste(bar, (pie.width, 0))
    else:
        combined = pie.copy()
    combined.save(combined_path)
    print(f"[charts] Combined chart saved -> {combined_path}")


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    # Collect test counts
    passed = terminalreporter.stats.get('passed', [])
    failed = terminalreporter.stats.get('failed', [])
    error = terminalreporter.stats.get('error', [])
    skipped = terminalreporter.stats.get('skipped', [])
    xfail = terminalreporter.stats.get('xfail', [])
    reruns = terminalreporter.stats.get('rerun', [])

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

    # Generate summary charts for Slack
    save_summary_charts({
        "passed":  len(passed),
        "failed":  len(failed),
        "skipped": len(skipped),
        "reruns":  len(reruns),
    })

@pytest.fixture(scope="session", autouse=True)
def global_presetup_fixture():
    """Truly run once before any tests (even with xdist)."""
    print("\n>>> Running global presetup before all tests <<<")
    # Your setup logic here
    yield
    print("\n>>> Global presetup teardown after all tests <<<")


def _uses_adminff(fspath) -> bool:
    """Return True if the module instantiates AdminFFPage anywhere."""
    try:
        return "AdminFFPage(" in Path(fspath).read_text(encoding="utf-8")
    except OSError:
        return False


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

    # Any module that instantiates AdminFFPage toggles feature flags and must
    # run last so it doesn't interfere with other parallel tests.
    adminff_files = {item.fspath for item in items if _uses_adminff(item.fspath)}
    regular, last = [], []
    for item in items:
        if item.fspath in adminff_files:
            last.append(item)
        else:
            regular.append(item)
    items[:] = regular + last


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
