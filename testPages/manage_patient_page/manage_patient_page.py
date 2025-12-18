import re
import time

from selenium.webdriver import Keys

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string
from user_inputs.user_data import UserData


class ManagePatientPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def validate_manage_patient_page(self):
        self.wait_for_page_to_load()
        self.wait_for_element("span_Patients", 50)
        time.sleep(10)
        self.wait_for_page_to_load()
        self.wait_for_element("tbody_patient", 100)


    def search_patient(self, fname, lname, mrn, username, sa_id, start=None, end=None, dose=None):
        full_name = fname+" "+lname
        self.type('input_search_patient', full_name)
        time.sleep(10)
        self.wait_for_page_to_load()
        self.wait_for_element('tbody_patient')
        self.wait_for_element('td_name')
        self.wait_for_element('td_username')

        name = self.get_text('td_name')
        username_value = self.get_text('td_username')
        mrn_value = self.get_text('td_mrn')
        sa_id_value = self.get_text("td_sa_id")
        print(name, username_value, mrn_value)
        assert name.strip() == full_name, "Name mismatch"
        assert username_value.strip() == username, "Username mismatch"
        if dose:
            doses_value = self.get_text('td_est_doses_remain')
            assert str(doses_value).strip() == str(dose), f"Doses mismatch {dose} and {doses_value}"
        assert mrn_value.strip() == mrn, "MRN mismatch"
        assert sa_id_value.strip() == sa_id, "SA ID mismatch"
        if start:
            start_value = self.get_text('td_start_date')
            assert start_value == start, f"Start Date mismatch {start} and {start_value}"
        if end:
            end_value = self.get_text('td_end_date')
            assert end_value == end, f"End Date mismatch {end} and {end_value}"


        print(f"All data matching: {name}, {username_value}, {mrn_value}, {sa_id_value}, {start}, {end}, {dose}")

    def open_patient(self, fname, lname):
        full_name = fname + " " + lname
        name = self.get_text('a_name')
        assert name.strip() == full_name, "Name mismatch"
        self.click('a_name')
        time.sleep(10)


    def open_inactive_tab(self):
        self.click("li_span_Inactive_tab")
        self.wait_for_page_to_load()
        self.wait_for_element("span_Patients", 50)
        time.sleep(10)
        self.wait_for_page_to_load()
        self.wait_for_element('k-opened-tabstrip-tab')
        tabname = self.get_text('k-opened-tabstrip-tab')
        assert tabname == "Inactive", "Inactive tab is not opened"
        print("Opened tab is Inactive")
        self.wait_for_element("tbody_patient", 100)

    def open_active_tab(self):
        self.click("li_span_Active_tab")
        self.wait_for_page_to_load()
        self.wait_for_element("span_Patients", 50)
        time.sleep(10)
        self.wait_for_page_to_load()
        self.wait_for_element('k-opened-tabstrip-tab')
        tabname = self.get_text('k-opened-tabstrip-tab')
        assert tabname == "Active", f"{tabname} is open and not Active"
        print("Opened tab is Active")
        self.wait_for_element("tbody_patient", 100)


    def open_test_tab(self):
        self.click("li_span_Test_tab")
        self.wait_for_page_to_load()
        self.wait_for_element("span_Patients", 50)
        self.wait_for_element('k-opened-tabstrip-tab')
        tabname = self.get_text('k-opened-tabstrip-tab')
        assert tabname == "Test", "Test tab is not opened"
        print("Opened tab is Test")
        self.wait_for_element("tbody_patient", 100)

    def open_first_patient(self):
        name = self.get_text('a_name')
        self.click('a_name')
        time.sleep(10)
        name = name.split(" ")
        fname = name[0]
        lname = name[1]
        return fname, lname

    def search_test_patients(self, name='pat_fn_'):
        self.type('input_search_patient', name)
        time.sleep(10)
        self.wait_for_page_to_load()
        self.wait_for_element('tbody_patient')
        self.wait_for_element('td_name')
        assert name in self.get_text('a_name'), f"Test patient {name} not displayed"
        print(f"Test patient {name} is displayed")



    def search_test_patients_not_present(self, name='pat_fn_'):
        self.type('input_search_patient', name)
        time.sleep(10)
        self.wait_for_page_to_load()
        self.wait_for_element('tbody_patient')
        self.wait_for_element('no_data')
        assert name not in self.get_text('no_data'), f"{name} is displayed for this Account"
        print(f"{name} is not displayed for this Account")

    def change_url(self, sa_id):
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
            self.wait_for_overlays_to_clear(5)
        except:
            print("No dialog present")
        url = self.get_current_url()
        parts = url.rstrip("/").split("/")
        parts[-1] = sa_id
        new_url = "/".join(parts)
        print(new_url)
        self.launch_url(new_url)
        self.wait_for_page_to_load()
        time.sleep(5)
        self.kendo_dialog_wait_open()
        text = self.kendo_dialog_get_text()
        print(text)
        assert UserData.access_warning in text, f"{UserData.access_warning} not present in {text}"
        print(f"{UserData.access_warning} is present in {text}")
        self.kendo_dialog_close()


    def get_sa_id(self):
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
            self.wait_for_overlays_to_clear(5)
        except:
            print("No dialog present")
        url = self.get_current_url()
        parts = url.rstrip("/").split("/")
        sa_id_value = parts[-1]
        print(sa_id_value)
        return sa_id_value

