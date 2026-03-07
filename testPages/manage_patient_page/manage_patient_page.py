import re
import time

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

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
        time.sleep(5)
        self.wait_for_page_to_load(50)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
        except Exception:
            print("popup not present")



    def open_inactive_tab(self):
        self.click("li_span_Inactive_tab")
        self.wait_for_page_to_load()
        self.wait_for_element("span_Patients", 50)
        time.sleep(20)
        self.wait_for_element('k-opened-tabstrip-tab')
        self.wait_for_element("tbody_patient", 100)
        self.unheal_all('k-opened-tabstrip-tab')
        time.sleep(5)
        tabname = self.get_text('k-opened-tabstrip-tab')
        print(tabname)
        assert tabname == "Inactive", "Inactive tab is not opened"
        print("Opened tab is Inactive")
        self.wait_for_element("tbody_patient", 100)

    def open_active_tab(self):
        self.click("li_span_Active_tab")
        self.wait_for_page_to_load()
        self.wait_for_element("span_Patients", 50)
        time.sleep(20)
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
        time.sleep(20)
        self.wait_for_page_to_load()
        self.wait_for_element('k-opened-tabstrip-tab')
        self.wait_for_element("tbody_patient", 100)
        self.unheal_all('k-opened-tabstrip-tab')
        time.sleep(5)
        tabname = self.get_text('k-opened-tabstrip-tab')
        print(tabname)
        assert tabname == "Test", "Test tab is not opened"
        print("Opened tab is Test")


    def open_first_patient(self):
        name = self.get_text('a_name')
        self.click('a_name')
        time.sleep(10)
        name = name.split(" ")
        fname = name[0]
        lname = name[1]
        return fname, lname

    def get_details_first_patient(self):
        name = self.get_text('a_name')
        name = name.split(" ")
        fname = name[0]
        lname = name[1]
        username_value = self.get_text('td_username')
        mrn_value = self.get_text('td_mrn')
        sa_id_value = self.get_text("td_sa_id")
        print(fname, lname, mrn_value, username_value, sa_id_value)
        return fname, lname, mrn_value, username_value, sa_id_value.upper()

    def search_test_patients(self, name='pat_fn'):
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


    def search_patient_with_partial_info(self, fname=None, lname=None, mrn=None, username=None, sa_id=None, any=None, multiple=1 , caps=False):
        if fname!=None or lname!=None:
            name = fname if fname else lname
            full_name = fname+" "+lname if fname and lname else name
            full_name = str(full_name).upper() if caps else full_name
            print(f"Searching for {full_name}")
            self.wait_for_element('tbody_patient', 50)
            for i in range(multiple):
                self.type('input_search_patient', full_name)
                time.sleep(5)
                self.wait_for_page_to_load()
                self.wait_for_element('tbody_patient')
                self.wait_for_text(full_name.lower(), 'a_name', 50)
                name = self.get_text('a_name')
                assert full_name.lower() in name.strip(), f"Name mismatch {name} and {full_name}"
                print(f"Correct patient with name {name} is displayed for {i} search")

        elif mrn != None:
            search_name=mrn
            self.wait_for_element('tbody_patient', 50)
            for i in range(multiple):
                self.type('input_search_patient', search_name)
                time.sleep(5)
                self.wait_for_page_to_load()
                self.wait_for_element('tbody_patient')

                self.wait_for_text(search_name.lower(), 'td_mrn', 50)
                mrn_value = self.get_text('td_mrn')
                assert search_name.lower() in mrn_value.strip(), f"MRN mismatch {mrn_value} and {search_name}"
                print(f"Correct patient with mrn {search_name} is displayed for {i} search")
        elif username != None:
            search_name = username
            self.wait_for_element('tbody_patient', 50)
            for i in range(multiple):
                self.type('input_search_patient', search_name)
                time.sleep(5)
                self.wait_for_page_to_load()
                self.wait_for_element('tbody_patient')
                self.wait_for_text(search_name.lower(), 'td_username', 50)
                username_value = self.get_text('td_username')
                assert search_name.lower() in username_value.strip(), f"Username mismatch {username_value} and {search_name}"
                print(f"Correct patient with username {search_name} is displayed for {i} search")
        elif sa_id != None:
            search_name = sa_id
            self.wait_for_element('tbody_patient', 50)
            for i in range(multiple):
                self.type('input_search_patient', search_name)
                time.sleep(5)
                self.wait_for_page_to_load()
                self.wait_for_element('tbody_patient')
                self.wait_for_text(search_name, 'td_sa_id', 50)
                sa_id_value = self.get_text("td_sa_id")
                assert search_name.lower() in sa_id_value.lower().strip(), f"SA ID mismatch {sa_id_value.lower().strip()} and {search_name.lower()}"
                print(f"Correct patient with SA ID {search_name} is displayed for {i} search")
        elif any != None:
            search_name = any
            self.wait_for_element('tbody_patient', 50)
            for i in range(multiple):
                self.type('input_search_patient', any)
                time.sleep(5)
                self.wait_for_page_to_load()
                self.wait_for_element('tbody_patient')
                rows = self.find_elements("tr_patient_rows")  # locator for all rows
                found = False
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")

                    for cell in cells:
                        cell_text = cell.text.strip().lower()
                        print(cell_text)

                        if search_name in cell_text:
                            found = True
                            print(f"'{any}' found in: {cell_text}")
                            break  # stop checking cells in this row

                assert found, f"'{any}' not found in any table cell"


        else:
            print("No search value provided")

    def search_and_sort_columns(self, name: str):
        self.type('input_search_patient', name)
        time.sleep(30)
        self.wait_for_page_to_load(60)
        self.wait_for_element('tbody_patient')

        total_cols = len(self.find_elements("table_header_sort"))
        print(f"Total sortable columns: {total_cols}")

        for index in range(1, total_cols + 1):
            if index == 3 or index == 4 or index == 7 or index == 8:
                print(f"Column {index} is not sortable. Skipping.")
                continue

            # ---------- FIRST CLICK ----------
            headers = self.find_elements("table_header_sort")
            header = headers[index - 1]
            # time.sleep(2)
            # self.driver.execute_script("arguments[0].click();", headers[index - 1])
            header.click()
            time.sleep(8)
            self.wait_for_page_to_load(50)

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

            time.sleep(3)
            # ---------- SECOND CLICK (REVERSE) ----------
            headers = self.find_elements("table_header_sort")
            header = headers[index - 1]
            header.click()
            # time.sleep(2)
            # self.driver.execute_script("arguments[0].click();", headers[index - 1])
            time.sleep(8)
            self.wait_for_page_to_load(50)

            headers = self.find_elements("table_header_sort")
            header = headers[index - 1]
            sort_type = header.get_attribute("aria-sort") or ""

            print(f"Column {index} sort type: {sort_type}")
            values = self._get_column_values(index)
            print(f"Column {index}, Row counts: {len(values)} values: {values}")

            if len(values) >= 2:
                processed = self.normalize_values(values)
                self.is_sorted(processed, sort_type)

    def get_total_pages(self):
        self.wait_for_element('tbody_patient')
        text = self.get_text('kendo-pager-info')
        text_list = text.split('of')
        print(text_list[-1].strip())
        return text_list[-1].strip()

    def search_test_patient(self, name='pat_fn'):
        self.type('input_search_staff', name)
        time.sleep(10)
        self.wait_for_page_to_load()
        self.wait_for_element('tbody_patient')
        self.wait_for_element('a_name')
        assert name in self.get_text('a_name'), f"Test staff {name} not displayed"
        print(f"Test staff {name} is displayed")

    def validate_patient_table(self, columns=UserData.patient_list_columns):
        self.wait_for_element('tbody_patient')
        for items in columns:
            assert self.is_element_visible(f"th_{items}"), f"Column {items} not present"
            print(f"Column {items} present")