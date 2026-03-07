import random
import time
from datetime import date, datetime
import re
from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string, fetch_random_digit
from user_inputs.user_data import UserData


class PatientPillCountPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def open_patient_pill_count_page(self):
        self.click('k-tabstrip-tab-Pill count', strict=True)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
        except Exception:
            print("popup not present")

    def verify_patient_pill_count_page(self):
        time.sleep(5)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
        except Exception:
            print("popup not present")
        self.wait_for_page_to_load()
        self.wait_for_element('k-opened-tabstrip-tab')
        state=self.get_attribute("k-tabstrip-tab-Pill count", "aria-selected", strict=True)
        self.unheal_all('k-opened-tabstrip-tab')
        time.sleep(3)
        tabname = self.get_text('k-opened-tabstrip-tab')
        print(tabname)
        # assert tabname == "Pill count", "Pill Count tab is not opened"
        assert state == True, "Pill Count tab is not opened"
        self.wait_for_element('span_ADD NEW PILL COUNT')
        self.wait_for_element('h3_Pill count')
        print("Opened tab is Pill count")