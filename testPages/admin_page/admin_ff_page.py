import re
import time

from requests.packages import target
from selenium.webdriver import Keys

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string
from user_inputs.user_data import UserData


class AdminFFPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)



    def validate_admin_ff_page(self):
        self.wait_for_element('kendo-dropdownlist-input-value-Client')
        self.wait_for_element('div_content')
        text = self.get_text('kendo-dropdownlist-input-value-Client')
        assert text == UserData.client, f"Correct Client {UserData.client} is not present"
        print(f"Correct Client {UserData.client} is not present")

    def set_ffs(self, ff_dict):
        for ff, toggle in ff_dict.items():
            print(ff, toggle)
            target = True if toggle == "ON" else False
            element = f"kendo-switch_{ff}"
            print(element, target)
            self.wait_for_element(element)
            was_on = self.kendo_switch_is_on(element, strict=True)
            print(f"[switch] {ff}: was_on={was_on}")
            if was_on == target:
                print(f"{ff} is already set to {target}")
            else:
                self.kendo_switch_set(element, target, strict=True)
                time.sleep(2)
                self.kendo_switch_wait(element, target, timeout=8, strict=True)
                # verify
                now_on = self.kendo_switch_is_on(element, strict=True)
                print(f"[switch] {ff}: now_on={now_on}")
        self.refresh()
        time.sleep(10)

    def double_check_ff(self, ff_dict):
        for ff, toggle in ff_dict.items():
            print(f"Current parameters: {ff}, {toggle}")
            element = f"kendo-switch_{ff}"
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
            print(f"[switch] {ff}: now_on={now_on}")
            assert now_on == target, f"Switch '{ff}' did not change to {target}"
            print("Waiting for sometime for the changes to reflect")
            time.sleep(30)

