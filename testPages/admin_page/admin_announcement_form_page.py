import re
import time
from datetime import datetime

from selenium.webdriver import Keys

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string
from user_inputs.user_data import UserData


class AdminAnnouncementFormPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def validate_announcement_page(self):
        self.wait_for_element('label_Choose_Client')
        self.wait_for_element('kendo-multiselect_Select_Client')
        self.wait_for_element('span_SAVE')
        print("Admin Announcement Form Page is now open")

    def toggle_for_status(self, toggle=None):
        was_on = self.kendo_switch_is_on('kendo-switch-Status')
        print(f"Status switch: was_on={was_on}")

        if toggle == "Active":
            target = True
        elif toggle == "Inactive":
            target = False
        else:
            # target = flipped state
            target = not was_on
        # set & wait for it to take effect (handles animations/re-render)
        self.kendo_switch_set('kendo-switch-Status', target)
        time.sleep(2)
        self.kendo_switch_wait('kendo-switch-Status', target, timeout=8)
            # verify
        now_on = self.kendo_switch_is_on('kendo-switch-Status')
        time.sleep(2)
        print(f"Status switch : now_on={now_on}")
        assert now_on == target, f"Status Switch did not change to {target}"
        return "Active" if now_on else "Inactive"


    def double_check_on_toggle(self, toggle):
        flag = self.get_attribute('kendo-switch-Status', 'aria-checked')
        target = True if toggle == "Active" else False
        if toggle == "Active" and flag == False:
            target = True
            self.click('kendo-switch-Status')
        elif toggle == "Inactive" and flag == True:
            target = False
            self.click('kendo-switch-Status')
        else:
            print(f"toggle {toggle} and toggle {toggle} matching")
        now_on = self.kendo_switch_is_on('kendo-switch-Status')
        print(f"Status switch: now_on={now_on}")
        assert now_on == target, f"Status Switch did not change to {target}"
        print("Waiting for sometime for the changes to reflect")
        time.sleep(2)

    def add_announcement(self, status='Active'):
        date_time = datetime.now().strftime("%B %d, %Y %I:%M %p")
        print(date_time)
        announcement_text = f"Announcement created via automation on {date_time}"
        self.wait_for_element('kendo-multiselect_Select_Client')
        self.click('kendo-multiselect_Select_Client')
        self.kendo_select("k-input-Select Client", text=UserData.client)
        # self.switch_to_frame('iframe')
        with self.within_frame('iframe'):
            self.wait_for_element('div_textbox')
            self.type('div_textbox', announcement_text)
            time.sleep(2)
        self.switch_to_default_content()
        status_now = self.toggle_for_status(status)
        print(status_now)
        self.double_check_on_toggle(status)
        self.click_robust('span_SAVE')
        try:
            self.click('button_Close')
            self.wait_for_invisible('button_Close')
        except:
            print('Form closed already')
        self.refresh()
        time.sleep(5)
        self.wait_for_page_to_load()
        return announcement_text, status, UserData.client

    def deactivate_the_announcements(self):
        status_now = self.toggle_for_status('Inactive')
        print(status_now)
        self.double_check_on_toggle('Inactive')
        self.click_robust('span_SAVE')
        try:
            self.click('button_Close')
            self.wait_for_invisible('button_Close')
        except Exception:
            print('Form closed already')
        self.refresh()
        time.sleep(5)
        self.wait_for_page_to_load()
        return status_now

