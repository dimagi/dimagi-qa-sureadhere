import json
import os

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumbase import BaseCase

class BasePage:
    def __init__(self, sb, page_name=None):
        self.sb = sb  # This is the SeleniumBase test instance (self from test class)
        self.driver = sb.driver
        self.page_name = page_name
        self.locators = self.load_page_locators(page_name) if page_name else {}

    def load_page_locators(self, page_name):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(current_dir, "self_healing_locators", f"{page_name}.json")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Locator file not found: {path}")

        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def get_locator(self, logical_name):
        locator_entry = self.locators.get(logical_name)
        if not locator_entry:
            raise Exception(f"Locator '{logical_name}' not found in {self.page_name}")
        return locator_entry.get("xpath") or self.try_all_possible_strategies(locator_entry)

    def try_all_possible_strategies(self, logical_name):
        locator_entry = self.locators.get(logical_name, {})
        for key in ["xpath", "id", "name", "css", "tag", "type", "class", "text", "placeholder", "aria-label"]:
            value = locator_entry.get(key)
            if value:
                try:
                    self.sb.wait_for_element(value, timeout=3)
                    return value
                except Exception:
                    continue
        raise Exception(f"No working locator found for '{logical_name}'")

    def try_alternative_locators(self, logical_name):
        locator_entry = self.locators.get(logical_name, {})
        alternatives = locator_entry.get("alternates", [])
        for alt_xpath in alternatives:
            try:
                self.sb.wait_for_element(alt_xpath, timeout=3)
                return alt_xpath
            except Exception:
                continue
        raise Exception(f"No working locator found for '{logical_name}'")

    def resolve_xpath(self, logical_name):
        try:
            xpath = self.get_locator(logical_name)
            self.sb.wait_for_element(xpath, timeout=5)
            return xpath
        except Exception:
            return self.try_all_possible_strategies(logical_name)

    def wait_for_element(self, logical_name, timeout=10):
        xpath = self.resolve_xpath(logical_name)
        self.sb.wait_for_element(xpath, timeout=timeout)

    def click(self, logical_name):
        xpath = self.resolve_xpath(logical_name)
        self.highlight(xpath)
        self.sb.click(xpath)

    def send_keys(self, logical_name, value):
        xpath = self.resolve_xpath(logical_name)
        self.highlight(xpath)
        self.sb.type(xpath, value)

    def get_text(self, logical_name):
        xpath = self.resolve_xpath(logical_name)
        return self.sb.get_text(xpath)

    def highlight(self, xpath):
        try:
            self.sb.highlight(xpath)
        except Exception:
            pass

    def wait_for_page_to_load(self, timeout=50):
        self.sb.wait_for_ready_state_complete(timeout=timeout)

    def is_element_visible(self, logical_name):
        xpath = self.resolve_xpath(logical_name)
        return self.sb.is_element_visible(xpath)

    def is_element_enabled(self, logical_name):
        xpath = self.resolve_xpath(logical_name)
        return self.sb.is_element_enabled(xpath)

    def wait_for_element_clickable(self, logical_name, timeout=10):
        xpath = self.resolve_xpath(logical_name)
        self.sb.wait_for_element_clickable(xpath, timeout=timeout)

    def select_option_by_text(self, logical_name, option_text):
        xpath = self.resolve_xpath(logical_name)
        self.sb.select_option_by_text(xpath, option_text)

    def element_exists(self, logical_name):
        try:
            xpath = self.resolve_xpath(logical_name)
            return self.sb.is_element_present(xpath)
        except Exception:
            return False

    def launch_url(self, url):
        self.sb.open(url)
        self.wait_for_page_to_load(50)

    def verify_page_title(self, title, timeout=50):
        WebDriverWait(self.sb.driver, timeout).until(EC.title_contains(title))
        actual_title = self.sb.get_title()
        print(f"Page title: {actual_title}")
        self.sb.assert_title(title)  # Or use self.assert_title_contains()