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


    def search_staff(self, fname=None, lname=None, email=None, phn=None, manager = UserData.default_managers, site=None):
        full_name = fname+" "+lname
        self.type('input_search_staff', full_name)
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element('tbody_staff')
        name = self.get_text('a_name')
        email_text = self.get_text('td_email')
        phn_number = self.get_text('td_phone_number')
        print(name, email_text, phn_number)

        if site:
            for item in manager:
                text = self.get_text(f"li_role_{item}", strict=True)
                print(text)
                assert site in text, f"{site} is not present for role {item}"
                print(f"{site} is present for role {item}")

        assert name.strip() == full_name, "Name mismatch"
        if email:
            assert email_text.strip() == email, "Email mismatch"
        if phn:
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

    def validate_active_tab(self):
        self.wait_for_page_to_load(50)
        self.wait_for_element('span_Active')
        text = self.get_text('li_Active')
        assert "Active" in text, "Active tab is not opened"
        print("Active tab is opened")

    def validate_test_tab(self):
        self.wait_for_page_to_load(50)
        self.wait_for_element('span_Active')
        text = self.get_text('li_Active')
        assert "Test" in text, "Active tab is not opened"
        print("Test tab is opened")

    def search_staff_with_partial_info(self, fname=None, lname=None, multiple=1 , caps=False):
        name = fname if fname else lname
        full_name = fname+" "+lname if fname and lname else name
        full_name = str(full_name).upper() if caps else full_name
        print(f"Searching for {full_name}")
        for i in range(multiple):
            self.type('input_search_staff', full_name)
            time.sleep(5)
            self.wait_for_page_to_load()
            self.wait_for_element('tbody_staff')
            name = self.get_text('a_name')
            assert full_name.lower() in name.strip(), f"Name mismatch {name} and {full_name}"
            print(f"Correct staff with name {name} is displayed for {i} search")
