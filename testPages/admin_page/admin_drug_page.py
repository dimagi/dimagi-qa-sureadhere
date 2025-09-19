import re
import time

from requests.packages import target
from selenium.webdriver import Keys

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string
from user_inputs.user_data import UserData


class AdminDrugPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def toggle_for_drugs(self, name, toggle):
        element = f"kendo-switch_{name}"
        self.wait_for_element(element)
        was_on = self.kendo_switch_is_on(element, strict=True)
        print(f"[switch] {name}: was_on={was_on}")

        target = True if toggle == "ON" else False
        # if toggle == "ON":
        #     target = False
        # elif toggle == "OFF":
        #     target = True
        # else:
        #     # target = flipped state
        #     target = not was_on
        print(f"Current target {target}")
        # set & wait for it to take effect (handles animations/re-render)
        self.kendo_switch_set(element, target, strict=True)
        time.sleep(2)
        self.kendo_switch_wait(element, target, timeout=8, strict=True)
            # verify
        now_on = self.kendo_switch_is_on(element, strict=True)
        self.refresh()
        time.sleep(10)
        print(f"[switch] {name}: now_on={now_on}")
        assert now_on == target, f"Switch '{name}' did not change to {target}"
        return ("ON" if now_on else "OFF"), name

    def double_check_on_toggle(self, name, toggle):
        print(f"Current parameters: {name}, {toggle}")
        element = f"kendo-switch_{name}"
        flag = self.get_attribute(element, 'aria-checked')
        target = True if toggle == "ON" else False
        if toggle == "ON" and flag == False:
            target = True
            self.click(element)
        elif toggle == "OFF" and flag == True:
            target = False
            self.click(element)
        else:
            print(f"toggle {toggle} and toggle {toggle} matching")
        now_on = self.kendo_switch_is_on(element, strict=True)
        print(f"[switch] {name}: now_on={now_on}")
        assert now_on == target, f"Switch '{name}' did not change to {target}"
        print("Waiting for sometime for the changes to reflect")
        time.sleep(30)

