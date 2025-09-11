import re
import time

from selenium.webdriver import Keys

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string
from user_inputs.user_data import UserData


class ManageStaffPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def validate_manage_staff_page(self):
        self.wait_for_page_to_load()
        self.wait_for_element("span_Manage_staff", 50)
        time.sleep(10)
        self.wait_for_page_to_load()
        self.wait_for_element("tbody_staff", 100)


    def search_staff(self, fname, lname, email, phn):
        full_name = fname+" "+lname
        self.type('input_search_staff', full_name)
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element('tbody_staff')
        name = self.get_text('a_name')
        email_text = self.get_text('td_email')
        phn_number = self.get_text('td_phone_number')
        print(name, email_text, phn_number)
        assert name.strip() == full_name, "Name mismatch"
        assert email_text.strip() == email, "Email mismatch"
        assert re.sub(r"\D+", "", phn_number) == re.sub(r"\D+", "", phn), "Phone mismatch"
        print(f"All data matching: {name}, {email_text}, {phn_number}")

    def open_staff(self, fname, lname):
        full_name = fname + " " + lname
        name = self.get_text('a_name')
        assert name.strip() == full_name, "Name mismatch"
        self.click('a_name')
        time.sleep(10)

    def open_inactive_tab(self):
        self.click("li_span_Inactive_tab")
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element("span_Manage_staff", 50)
        self.wait_for_element("tbody_staff", 100)
        self.wait_for_element('a_name', 50)

    def open_test_tab(self):
        self.click("li_span_Test_tab")
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element("span_Manage_staff", 50)
        self.wait_for_element("tbody_staff", 100)
        self.wait_for_element('a_name', 50)


