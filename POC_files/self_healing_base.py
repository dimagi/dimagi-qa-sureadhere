from seleniumbase import BaseCase
from POC_files.locator_manager import LocatorManager

class SelfHealingBase(BaseCase):
    def smart_click(self, key, page):
        lm = LocatorManager()
        locators = lm.get_all_locators(key, page)
        for locator in locators:
            try:
                self.click(locator)
                lm.remember_successful_locator(key, locator)
                return
            except Exception:
                self.log(f"Click failed for: {locator}")
        raise Exception(f"All locators failed for {key} on {page}")

    def smart_type(self, key, text, page):
        lm = LocatorManager()
        locators = lm.get_all_locators(key, page)
        for locator in locators:
            try:
                self.type(locator, text)
                lm.remember_successful_locator(key, locator)
                return
            except Exception:
                self.log(f"Type failed for: {locator}")
        raise Exception(f"All locators failed for {key} on {page}")
