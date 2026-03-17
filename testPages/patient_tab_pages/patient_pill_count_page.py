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
        self.wait_for_page_to_load()

    def verify_patient_pill_count_page_presence(self, flag):
        time.sleep(5)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
        except Exception:
            print("popup not present")
            print(self.resolve('k-tabstrip-tab-Pill count'))
        if flag:
            assert self.is_element_visible('k-tabstrip-tab-Pill count', strict=True), 'Pill count is not present'
            print('Pill count tab is present')
        else:
            assert not self.is_element_visible('k-tabstrip-tab-Pill count', strict=True), 'Pill count is present'
            print('Pill count tab is not present')


    def verify_patient_pill_count_page(self):
        time.sleep(5)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
        except Exception:
            print("popup not present")
        self.wait_for_page_to_load()
        self.refresh()
        time.sleep(10)
        self.wait_for_page_to_load()
        self.wait_for_element('k-opened-tabstrip-tab')
        state=self.get_attribute("k-tabstrip-tab-Pill count", "aria-selected", strict=True)
        self.unheal_all('k-opened-tabstrip-tab')
        time.sleep(3)
        tabname = self.get_text('k-opened-tabstrip-tab')
        print(tabname, state)
        # assert tabname == "Pill count", "Pill Count tab is not opened"
        # assert state == True, "Pill Count tab is not opened"
        self.wait_for_element('span_ADD NEW PILL COUNT')
        self.wait_for_element('h3_Pill count')
        assert self.is_element_visible("span_ADD NEW PILL COUNT"), "Pill Count tab is not opened"
        print("Opened tab is Pill count")

    def verify_pill_count_error(self):
        self.wait_for_element('div_pill_count_error', strict=True)
        print(self.get_text('div_pill_count_error', strict=True))
        assert self.is_element_visible('div_pill_count_error', strict=True), "Regiment Approval error not present"
        print("Regiment Approval error present")

    def add_pill_count(self, drug_name):
        date_list = []
        self.click_robust('span_ADD NEW PILL COUNT')
        time.sleep(2)
        self.wait_for_element('button_ADD DRUG')

        today = self.today_date()
        visit_date = today
        return_date = self.calculate_date(visit_date, 1)
        formated_visit_date = self.format_full_mdY(visit_date)
        # if self.is_element_visible_rendered('div_title_custom', text=formated_visit_date):
        #     visit_date = self.calculate_date(today, 1)
        #     return_date = self.calculate_date(visit_date, 2)
        #     formated_visit_date = self.format_full_mdY(visit_date)
        # else:
        #     print("Date is not already present")
        self.type('input_visit_date', value=visit_date)
        for i, drug in enumerate(drug_name):
            row = i + 1
            # If the row input does not exist → create it
            if self.is_element_present_rendered("drug_name_input", index=row):
                print(f"Row {row} is present")
            else:
                print("Adding new row")
                self.click_robust('button_ADD DRUG')
                time.sleep(1)

            self.type_rendered('drug_name_input', value=drug_name[i], index=row)
            self.type_rendered('input_Date dispensed', value=visit_date, index=row)

            self.type_rendered('input_Pills dispensed', value='5', index=row)
            self.type_rendered('input_Date of return', value=return_date, index=row)
            self.type_rendered('input_Pills returned', value='1', index=row)
            self.type_rendered('input_damaged_lost_pills', value='1', index=row)
            try:
                if drug_name[i] == "Quabodepistat":
                    self.type('input_Kit Number', value=f"{fetch_random_digit(start=1, end=200)}")
            except:
                print("No kit number field present")

        date_list.append(formated_visit_date)

        self.click_robust('span_SAVE')
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
        except Exception:
            print("popup not present")
        self.wait_for_page_to_load()
        time.sleep(2)
        assert self.is_element_visible_rendered('div_title_custom', text=formated_visit_date)

        titles=self.get_elements_texts('div_title')
        drug_details = self.get_elements_texts('div_drug_rows')
        print(titles, date_list)
        print(drug_details)

        assert all(
            any(drug.lower() in detail.lower() for detail in drug_details)
            for drug in drug_name
            ), f"{drug_name} not all present in {drug_details}"
        print(f"{drug_name} all present in {drug_details}")
        assert all(dates in titles for dates in date_list), f"{date_list} not in {titles}"
        print(f"{date_list} in {titles}")

        return date_list, visit_date, return_date

    def edit_pill_count(self, date_list, drug_name, visit_date, return_date):
        date_list_new = []
        for item in date_list:
            self.js_click_rendered('edit_title_custom', text=item)
            time.sleep(10)
            visit_date_current = self.calculate_date(visit_date, 1)
            return_date_current = self.calculate_date(return_date, 1)
            self.type('input_visit_date', value=visit_date_current)

            for i, drug in enumerate(drug_name):
                row = i + 1
                # If the row input does not exist → create it
                self.type_rendered('input_Pills dispensed', value='5', index=row)
                self.type_rendered('input_Date of return', value=return_date_current, index=row)
                self.type_rendered('input_Pills returned', value='2', index=row)
                self.type_rendered('input_damaged_lost_pills', value='0', index=row)
                try:
                    kit = self.get_value('input_Kit Number')
                    new_kit = f"1{kit}"
                    print(kit, new_kit)
                    self.type('input_Kit Number', value=new_kit)
                except:
                    print("No kit number field present")

            date_visit = self.get_value('input_visit_date')
            formated_visit_date = self.format_full_mdY(date_visit)
            date_list_new.append(formated_visit_date)

            self.click_robust('span_SAVE')
            try:
                self.kendo_dialog_wait_open()  # no title constraint
                self.kendo_dialog_click_button("Ok")
            except Exception:
                print("popup not present")
            self.wait_for_page_to_load()
            time.sleep(2)
            self.wait_for_page_to_load()
            assert self.is_element_visible_rendered('div_title_custom', text=formated_visit_date)

        titles = self.get_elements_texts('div_title')
        drug_details = self.get_elements_texts('div_drug_rows')
        print(titles, date_list_new)
        print(drug_details)

        assert all(dates in titles for dates in date_list_new), f"{date_list_new} not in {titles}"
        print(f"{date_list_new} in {titles}")
        assert all(
            any(drug.lower() in detail.lower() for detail in drug_details)
            for drug in drug_name
            ), f"{drug_name} not all present in {drug_details}"
        print(f"{drug_name} all present in {drug_details}")
        return date_list_new

    def delete_pill_count(self, date_list, drug_name):
        time.sleep(3)
        for item in date_list:
            while True:
                self.js_click_rendered('edit_title_custom', text=item)
                time.sleep(10)
                self.wait_for_element('span_delete_pill')
            # delete_btns = self.find_elements('span_delete_pill')
            # print(len(delete_btns))
            # assert len(drug_name)==len(delete_btns), "Correct counts of delete buttons not present"
            # print("Correct counts of delete buttons present")
            # while True:
                delete_btns = self.find_elements('span_delete_pill')

                if not delete_btns:
                    break

                delete_btns[0].click()

                try:
                    self.kendo_dialog_wait_open()
                    self.kendo_dialog_click_button("Ok")
                except Exception:
                    print("popup not present")

                time.sleep(2)

            if self.is_element_present('span_SAVE'):
                self.click_robust('span_SAVE')
                try:
                    self.kendo_dialog_wait_open()  # no title constraint
                    self.kendo_dialog_click_button("Ok")
                except Exception:
                    print("popup not present")
                self.wait_for_page_to_load()
                time.sleep(2)
            else:
                print("Save button not present")

        titles = self.get_elements_texts('div_title')
        drug_details = self.find_elements('div_drug_rows')
        print(titles, date_list)
        print(len(drug_details))

        assert all(dates in titles for dates in date_list), f"{date_list} not in {titles}"
        print(f"{date_list} in {titles}")
        assert len(drug_details) == 0, f"{drug_name} still present"
        print(f"{drug_name} not present")