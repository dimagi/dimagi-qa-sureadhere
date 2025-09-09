from pathlib import Path

from appium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
import time

from common_utilities.path_settings import PathSettings
from user_inputs.user_data import UserData

""""Contains test page elements and functions related to the app installation and form submission on mobile"""


import os, json, subprocess

def bstack_upload_apk_with_curl(apk_path: str, bs_user: str, bs_key: str, custom_id: str | None = None) -> str:
    """
    Uploads an APK to BrowserStack App Automate using curl and returns the bs:// app_url.
    - apk_path: absolute/relative path to your APK (e.g., user_inputs/sureadhere.apk)
    - bs_user / bs_key: BrowserStack credentials
    - custom_id (optional): stable alias so your code can keep referring to the same id
    Raises RuntimeError on any failure.
    """
    apk_path = os.path.abspath(apk_path)
    print(apk_path)
    if not os.path.exists(apk_path):
        raise RuntimeError(f"APK not found at: {apk_path}")

    cmd = [
        "curl", "-sS",
        "-u", f"{bs_user}:{bs_key}",
        "-X", "POST",
        "https://api-cloud.browserstack.com/app-automate/upload",
        "-F", f'file=@"{apk_path}"'
    ]
    if custom_id:
        cmd += ["-F", f"custom_id={custom_id}"]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"curl failed (code {res.returncode}): {res.stderr or res.stdout}")

    try:
        payload = json.loads(res.stdout.strip() or "{}")
    except json.JSONDecodeError:
        raise RuntimeError(f"Unexpected response from BrowserStack: {res.stdout}")

    app_url = payload.get("app_url")
    if isinstance(app_url, str) and app_url.startswith("bs://"):
        return app_url

    # If you used a custom_id and the server says “already uploaded”, you can still use bs://<custom_id>.
    err = (payload.get("error") or "").lower()
    if custom_id and ("duplicate" in err or "already" in err):
        return f"bs://{custom_id}"

    raise RuntimeError(f"Upload failed: {payload}")


class Android:

    def __init__(self, settings):
        # This sample code uses the Appium python client v2
        # pip install Appium-Python-Client
        # Then you can paste this into a file and simply run with Python
        bs_user = settings["bs_user"]
        bs_key = settings["bs_key"]

        apk_path = Path(PathSettings.ROOT) / "user_inputs" / "app-release3.2.14-symptoms.apk"

        print(f"[DEBUG] __file__={__file__}")
        print(f"[DEBUG] PROJECT_ROOT={PathSettings.ROOT}")
        print(f"[DEBUG] APK_PATH={apk_path}")
        assert os.path.exists(apk_path), f"APK not found at: {apk_path}"

        bs_app_url = bstack_upload_apk_with_curl(
            apk_path=apk_path,  # <-- your pulled file
            bs_user=bs_user,
            bs_key=bs_key,
            # custom_id="sureadhere-local"  # optional but handy
            )
        self.options = UiAutomator2Options().load_capabilities({
            # Specify device and os_version for testing
            "platformName": "android",
            "appium:platformVersion": "15.0",
            "appium:deviceName": "Google Pixel 9",
            "appium:automationName": "UIAutomator2",

            # Set URL of the application under test
            "appium:app": bs_app_url,

            "appium:autoGrantPermissions": "true",
            "appium:newCommandTimeout": 3600,

            # Set other BrowserStack capabilities
            'bstack:options': {
                "projectName": "SureAdhere - Project",
                "buildName": "Build SA",
                "sessionName": "SureAdhere Tests",
                "userName": bs_user,
                "accessKey": bs_key

            }
        })

        # Initialize the remote Webdriver using BrowserStack remote URL
        # and desired capabilities defined above
        self.driver = webdriver.Remote(
            "https://hub-cloud.browserstack.com:443/wd/hub",
            options=self.options
        )
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 20)

        # Locator
        self.sa_logo = "com.dimagi.sureadhere:id/logo"
        self.staging_option = "//android.widget.TextView[@text='Staging']"
        self.username = "com.dimagi.sureadhere:id/username"
        self.pin = "com.dimagi.sureadhere:id/pin"
        self.login_button = "com.dimagi.sureadhere:id/login_button"
        self.take_video = "//android.widget.TextView[@text='Take Video']"
        self.start_tracking = "//android.widget.TextView[@text='Start Tracking']"
        self.grant_permission = "//android.widget.TextView[@text='Grant Permission']"
        self.submit = "//android.widget.TextView[@text='Submit']"
        self.submit_complete = "//android.widget.TextView[@text='Submission complete']"
        self.submission_status = "//android.widget.TextView[@text='Submission Status']"
        self.status = "//android.widget.TextView[@text='Status']"
        self.messages = "//android.widget.TextView[@text='Messages']"
        self.outgoing_message = "com.dimagi.sureadhere:id/outgoing_message"
        self.send_button = "com.dimagi.sureadhere:id/send_button"
        self.incoming_message = "com.dimagi.sureadhere:id/content"
        self.all_messages = "com.dimagi.sureadhere:id/messages"
        self.go_back = "//android.widget.ImageButton[@content-desc='Go Back']"

    def click_xpath(self, locator):
        element = self.driver.find_element(AppiumBy.XPATH, locator)
        element.click()

    def click_id(self, locator):
        element = self.driver.find_element(AppiumBy.ID, locator)
        element.click()

    def send_text_xpath(self, locator, user_input):
        element = self.driver.find_element(AppiumBy.XPATH, locator)
        element.send_keys(user_input)

    def send_text_id(self, locator, user_input):
        element = self.driver.find_element(AppiumBy.ID, locator)
        element.send_keys(user_input)

    def long_press(self, element, duration):
        try:
            self.driver.execute_script(
                "mobile: longClickGesture",
                {"elementId": element.id, "duration": duration}
                )
            return
        except Exception:
            pass

    def select_environment(self, url, min_secs= 7, max_secs= 10):
        if 'banner' in url:
            env = 'Staging'
        logo = self.wait.until(EC.presence_of_element_located((AppiumBy.ID, self.sa_logo)))
        for dur_ms in (int(min_secs * 1000), int(max_secs * 1000)):
            self.long_press(logo, dur_ms)
            try:
                self.wait.until(EC.visibility_of_element_located((AppiumBy.XPATH, self.staging_option)))
            except TimeoutException:
                # not visible yet—retry with a longer press
                continue
        self.click_xpath(self.staging_option)

    def login_patient(self, username, pin):
        self.wait.until(EC.visibility_of_element_located((AppiumBy.ID, self.username)))
        self.send_text_id(self.username, username)
        self.send_text_id(self.pin, pin)
        self.click_id(self.login_button)
        self.wait.until(EC.visibility_of_element_located((AppiumBy.XPATH, self.take_video)))



    def close_android_driver(self):
        self.driver.quit()
