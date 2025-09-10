import datetime
from pathlib import Path

from appium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
import time

from common_utilities.generate_random_string import fetch_random_string
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
        self.start_tracking = "//android.widget.Button[@text='Start Tracking']"
        self.grant_permission = "//android.widget.Button[@text='Grant Permission']"
        self.submit = "//android.widget.Button[@text='Submit']"
        self.submit_complete = "//android.widget.TextView[@text='Submission complete']"
        self.submission_status = "//android.widget.TextView[@text='Submission Status']"
        self.status = "//android.widget.TextView[@text='Status']"
        self.messages = "//android.widget.TextView[@text='Messages']"
        self.outgoing_message = "com.dimagi.sureadhere:id/outgoing_message"
        self.send_button = "com.dimagi.sureadhere:id/send_button"
        self.incoming_message = "com.dimagi.sureadhere:id/content"
        self.all_messages = "com.dimagi.sureadhere:id/messages"
        self.go_back = "Go Back"
        self.text_view = "//android.widget.TextView"
        self.more_options = "More options"
        self.logout = "//android.widget.TextView[@text()='Logout']"

    def click_xpath(self, locator):
        element = self.driver.find_element(AppiumBy.XPATH, locator)
        element.click()

    def click(self, locator):
        element = self.driver.find_element(*locator)
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

    def get_text(self, locator):
        element = self.driver.find_element(*locator)
        element_text = element.text
        print(element_text)
        return element_text

    def is_present(self, locator):
        try:
            element = self.driver.find_element(*locator)
            is_displayed = True
        except NoSuchElementException:
            is_displayed = False
        return bool(is_displayed)

    def long_press(self, element, duration):
        try:
            self.driver.execute_script(
                "mobile: longClickGesture",
                {"elementId": element.id, "duration": duration}
                )
            return
        except Exception:
            pass

    def grant_permissions_if_needed(self):
        # Try a few rounds (camera + mic often stack)
        allow_ids = [
            "com.android.permissioncontroller:id/permission_allow_foreground_only_button",
            "com.android.permissioncontroller:id/permission_allow_one_time_button",
            "com.android.permissioncontroller:id/permission_allow_button",
            "com.android.permissioncontroller:id/permission_allow_always_button",
            "com.android.packageinstaller:id/permission_allow_button",
            ]
        allow_texts = ["Allow", "ALLOW", "While using the app", "Allow only this time", "OK", "Continue", "I agree"]
        for _ in range(3):
            clicked = False
            # by id first
            for rid in allow_ids:
                els = self.driver.find_elements(AppiumBy.ID, rid)
                if els:
                    els[0].click();
                    time.sleep(0.4);
                    clicked = True;
                    break
            if clicked: continue
            # by text fallback
            for txt in allow_texts:
                try:
                    el = self.driver.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().textContains("{txt}")'
                        )
                    el.click();
                    time.sleep(0.4);
                    clicked = True;
                    break
                except Exception:
                    pass
            if not clicked:
                # no dialog right now
                return

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


    def record_video_and_submit(self, record_secs: int = 6, timeout: int = 90):
        # --- app flow ---
        self.wait.until(EC.visibility_of_element_located((AppiumBy.XPATH, self.take_video)))
        self.click_xpath(self.take_video)
        time.sleep(1)
        self.wait.until(EC.visibility_of_element_located((AppiumBy.XPATH, self.start_tracking)))
        self.click_xpath(self.start_tracking)
        time.sleep(1)
        try:
            self.wait.until(EC.visibility_of_element_located((AppiumBy.XPATH, self.grant_permission)))
            self.click_xpath(self.grant_permission)
            time.sleep(1)
        except:
            print("Grant Permission is not present")
        self.record_video(record_secs=8)
        time.sleep(1)
        self.wait.until(EC.visibility_of_element_located((AppiumBy.XPATH, self.submit)))
        self.click_xpath(self.submit)
        time.sleep(10)
        self.wait.until(EC.visibility_of_element_located((AppiumBy.XPATH, self.submission_status)))

        self.click((AppiumBy.ACCESSIBILITY_ID, self.go_back))


    def record_video(self, record_secs: int = 6, timeout: int = 30):

        # Tap the record/start button
        start_btn = self.wait.until(EC.element_to_be_clickable((AppiumBy.ID, "record_button")))
        start_btn.click()

        # Hold for N seconds
        self.driver.implicitly_wait(0)  # avoid implicit poll interfering
        time.sleep(record_secs)

        # Tap the stop button
        stop_btn = self.wait.until(EC.element_to_be_clickable((AppiumBy.ID, "stop_button")))
        stop_btn.click()

        return stop_btn

    def send_messages(self):
        self.wait.until(EC.visibility_of_element_located((AppiumBy.XPATH, self.messages)))
        self.click_xpath(self.messages)
        self.wait.until(EC.visibility_of_element_located((AppiumBy.ID, self.outgoing_message)))
        send_text = "Sending from phone "+fetch_random_string()
        self.send_message_and_verify(send_text)
        time.sleep(3)
        print(self.get_last_message_text())
        print(self.get_last_outgoing_text())
        self.click((AppiumBy.ACCESSIBILITY_ID, self.go_back))
        return send_text

    def read_messages(self, msg):
        self.wait.until(EC.visibility_of_element_located((AppiumBy.XPATH, self.messages)))
        self.click_xpath(self.messages)
        new_text=self.get_last_message_text()
        assert msg in new_text, f"Messages mismatch. {msg} not in {new_text}"
        print(f"{msg} found in {new_text}")

        self.click((AppiumBy.ACCESSIBILITY_ID, self.go_back))

    def send_message_and_verify(self, text: str, timeout: int = 15):
        # Make sure we’re in native context
        try:
            if "NATIVE_APP" not in self.driver.current_context:
                self.driver.switch_to.context("NATIVE_APP")
        except Exception:
            pass

        # 1) Focus + type
        field = self.wait.until(EC.element_to_be_clickable((AppiumBy.ID, self.outgoing_message)))
        try:
            field.clear()
        except Exception:
            pass
        field.send_keys(text)

        # Commit text / hide keyboard if it covers Send
        try:
            self.driver.execute_script("mobile: performEditorAction", {"action": "done"})
        except Exception:
            pass
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass

        # 2) Tap Send
        self.wait.until(EC.element_to_be_clickable((AppiumBy.ID, self.send_button))).click()

        # 3) Verify it appeared in the thread (adjust if needed)
        return self.wait.until(EC.presence_of_element_located((AppiumBy.ID, self.all_messages)))

    def scroll_thread_to_bottom(self):
        """Best-effort scroll to the bottom of the message list."""
        try:
            self.driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiScrollable(new UiSelector().resourceId("{self.all_messages}"))'
                f'.scrollToEnd(5)'
                )
        except Exception:
            pass  # not scrollable or already at bottom

    def get_all_message_texts(self, timeout: int = 20):
        """Return all non-empty bubble texts in order."""
        # Ensure the list exists
        self.wait.until(EC.presence_of_element_located((AppiumBy.ID, self.all_messages)))
        self.scroll_thread_to_bottom()
        bubbles = self.driver.find_elements(AppiumBy.ID, self.incoming_message)
        return [b.text for b in bubbles if (b.text or "").strip()]

    def get_last_message_text(self, timeout: int = 20):
        """Return the last (bottom-most) message text."""
        texts = self.get_all_message_texts(timeout=timeout)
        return texts[-1] if texts else None

    def wait_for_new_message(self, previous_count: int, timeout: int = 30):
        """Block until a new bubble appears and return the new text(s)."""

        def _count_changed(_):
            self.scroll_thread_to_bottom()
            return len(self.driver.find_elements(AppiumBy.ID, self.incoming_message)) > previous_count

        self.wait.until(_count_changed)
        self.scroll_thread_to_bottom()
        bubbles = self.driver.find_elements(AppiumBy.ID, self.incoming_message)
        return [b.text for b in bubbles[previous_count:] if (b.text or "").strip()]

    # --- optional: incoming vs outgoing (heuristic by alignment) -----------------

    def get_messages_with_direction(self, timeout: int = 20):
        """
        Return a list of dicts: {"text": str, "direction": "incoming"|"outgoing"}.
        Heuristic: bubbles on the RIGHT half are treated as outgoing.
        """
        
        self.wait.until(EC.presence_of_element_located((AppiumBy.ID, self.all_messages)))
        self.scroll_thread_to_bottom()

        bubbles = self.driver.find_elements(AppiumBy.ID, self.incoming_message)
        width = self.driver.get_window_size()["width"]
        out = []
        for b in bubbles:
            if not (b.text or "").strip():
                continue
            center_x = b.rect["x"] + b.rect["width"] / 2.0
            direction = "outgoing" if center_x > (width / 2.0) else "incoming"
            out.append({"text": b.text, "direction": direction})
        return out

    def get_last_incoming_text(self, timeout: int = 20):
        for item in reversed(self.get_messages_with_direction(timeout=timeout)):
            if item["direction"] == "incoming":
                return item["text"]
        return None

    def get_last_outgoing_text(self, timeout: int = 20):
        for item in reversed(self.get_messages_with_direction(timeout=timeout)):
            if item["direction"] == "outgoing":
                return item["text"]
        return None
    
    def close_android_driver(self):
        self.driver.quit()
