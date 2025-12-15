import re
import time

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

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
        global full_name
        self.wait_for_element('a_name')
        if email:
            self.type('input_search_staff', email)
        else:
            full_name = fname+" "+lname
            self.type('input_search_staff', full_name+Keys.ENTER)
        time.sleep(15)
        self.wait_for_page_to_load(50)
        self.wait_for_element('tbody_staff')
        name = self.get_text('a_name')
        email_text = self.get_text('td_email')
        phn_number = self.get_text('td_phone_number')
        print(name, email_text, phn_number)

        if site and manager is not None:
            for item in manager:
                text = self.get_text(f"li_role_{item}", strict=True)
                print(text)
                assert site in text, f"{site} is not present for role {item}"
                print(f"{site} is present for role {item}")
        if fname and lname:
            assert name.strip() == full_name, f"Name mismatch {name.strip()} and {full_name}"
        if email:
            assert email_text.strip() == email, "Email mismatch"
        if phn:
            assert re.sub(r"\D+", "", phn_number) == re.sub(r"\D+", "", phn), "Phone mismatch"
        print(f"All data matching: {name}, {email_text}, {phn_number}")

    def search_staff_with_email(self, email=None):
        self.type('input_search_staff', email)
        time.sleep(15)
        self.wait_for_page_to_load(50)
        self.wait_for_element('tbody_staff')
        email_text = self.get_text('td_email')

        assert email_text.strip() == email, "Email mismatch"

    def open_staff(self, fname, lname):
        full_name = fname + " " + lname
        name = self.get_text('a_name')
        assert name.strip() == full_name, "Name mismatch"
        self.click('a_name')
        time.sleep(10)

    def get_first_staff_name(self):
        name = self.get_text('a_name')
        fname, lname = str(name).split(" ")
        print(fname, lname)
        return fname, lname

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

    def validate_inactive_tab(self):
        self.wait_for_page_to_load(50)
        self.wait_for_element('span_Active')
        text = self.get_text('li_Active')
        assert "Inactive" in text, "Inactive tab is not opened"
        print("Inactive tab is opened")

    def search_staff_with_partial_info(self, fname=None, lname=None, multiple=1 , caps=False):
        name = fname if fname else lname
        full_name = fname+" "+lname if fname and lname else name
        full_name = str(full_name).upper() if caps else full_name
        print(f"Searching for {full_name}")
        self.wait_for_element('tbody_staff', 50)
        for i in range(multiple):
            self.type('input_search_staff', full_name)
            time.sleep(10)
            self.wait_for_page_to_load()
            self.wait_for_element('tbody_staff')
            self.wait_for_text(full_name.lower(), 'a_name', 50)
            name = self.get_text('a_name')
            assert full_name.lower() in name.strip(), f"Name mismatch {name} and {full_name}"
            print(f"Correct staff with name {name} is displayed for {i} search")

    def search_and_sort_columns(self, name: str):
        self.type('input_search_staff', name)
        self.wait_for_page_to_load()
        self.wait_for_element('tbody_staff')

        total_cols = len(self.find_elements("table_header_sort"))
        print(f"Total sortable columns: {total_cols}")

        for index in range(1, total_cols + 1):
            if index == 3:
                print("Column 3 is not sortable. Skipping.")
                continue

            # ---------- FIRST CLICK ----------
            headers = self.find_elements("table_header_sort")
            header = headers[index - 1]
            header.click()
            self.wait_for_page_to_load()

            headers = self.find_elements("table_header_sort")
            header = headers[index - 1]
            sort_type = header.get_attribute("aria-sort") or ""

            if sort_type not in ("ascending", "descending"):
                print(f"Column {index} has no valid sort state. Skipping.")
                continue

            print(f"Column {index} sort type: {sort_type}")
            values = self._get_column_values(index)
            print(f"Column {index}, Row counts: {len(values)} values: {values}")

            if len(values) >= 2:
                processed = self.normalize_values(values)
                self.is_sorted(processed, sort_type)

            # ---------- SECOND CLICK (REVERSE) ----------
            headers = self.find_elements("table_header_sort")
            header = headers[index - 1]
            header.click()
            self.wait_for_page_to_load()

            headers = self.find_elements("table_header_sort")
            header = headers[index - 1]
            sort_type = header.get_attribute("aria-sort") or ""

            print(f"Column {index} sort type: {sort_type}")
            values = self._get_column_values(index)
            print(f"Column {index}, Row counts: {len(values)} values: {values}")

            if len(values) >= 2:
                processed = self.normalize_values(values)
                self.is_sorted(processed, sort_type)

    def search_test_staff(self, name='test_f'):
        self.type('input_search_staff', name)
        time.sleep(10)
        self.wait_for_page_to_load()
        self.wait_for_element('tbody_staff')
        self.wait_for_element('a_name')
        assert name in self.get_text('a_name'), f"Test staff {name} not displayed"
        print(f"Test staff {name} is displayed")

    def search_test_staff_not_present(self, name='test_f'):
        self.type('input_search_staff', name)
        time.sleep(10)
        self.wait_for_page_to_load()
        self.wait_for_element('tbody_staff')
        self.wait_for_element('no_data')
        assert name not in self.get_text('no_data'), f"{name} is displayed for this Account"
        print(f"{name} is not displayed for this Account")


