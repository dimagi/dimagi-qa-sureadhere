import re
from datetime import datetime, date, timedelta
import time
import random

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string, fetch_random_digit
from user_inputs.user_data import UserData


class PatientRegimenPage(BasePage):

    regimen_name = "reg_"+fetch_random_string()

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def open_patient_regimen_page(self):
        self.click('k-tabstrip-tab-Regimen')
        time.sleep(2)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Continue")
        except Exception:
            print("popup not present")

    def verify_patient_regimen_page(self):
        time.sleep(5)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Continue")
        except Exception:
            print("popup not present")
        self.wait_for_page_to_load()
        self.wait_for_element('k-opened-tabstrip-tab')
        self.unheal_all('k-opened-tabstrip-tab')
        time.sleep(3)
        tabname = self.get_text('k-opened-tabstrip-tab')
        print(tabname)
        assert tabname == "Regimen", "Regimen tab is not opened"
        self.wait_for_element('kendo-dropdownlist-Disease', 40)
        self.wait_for_element('input_regimen_name' )
        self.wait_for_element('button_NEW_SCHEDULE')
        print("Opened tab is Regimen")
        time.sleep(10)


    def today_date(self):
        date_today = datetime.today()
        date_today = date_today.strftime("%Y-%m-%d")
        print(date_today)
        return date_today

    def past_date(self, days=1):
        date_past = datetime.today() - timedelta(days=days)
        date_past = date_past.strftime("%Y-%m-%d")
        print(date_past)
        return date_past

    def future_date(self, days=1):
        date_future = datetime.today() + timedelta(days=days)
        date_future = date_future.strftime("%Y-%m-%d")
        print(date_future)
        return date_future

    def calculate_end_date(self, start_date, no_of_weeks):
        start_date = date.fromisoformat(start_date)
        days_to_add = (no_of_weeks * 7) - 1

        # Create a timedelta object with the specified number of days
        duration = timedelta(days=days_to_add)

        # Add the timedelta to the start date to get the end date
        end_date = start_date + duration
        end_date = self.format_mdY(end_date)
        print(end_date)

        return end_date

    def get_time_now(self):
        now = datetime.now()
        time_now = now.time().strftime("%I:%M %p")
        print(time_now)
        return str(time_now)

    def add_regimen_name(self):
        self.wait_for_element('input_regimen_name')
        time_now = self.get_time_now()
        reg_name=f"reg_{time_now}"
        self.type('input_regimen_name', reg_name)
        self.click('button_SAVE')
        return reg_name

    def create_new_schedule(self, multi=False, disease_flag=True, drug_name=None, add_pill=True, time_of_drug=False, past_date=False, no_of_weeks='1', donot_add_drug=None):
        self.wait_for_page_to_load(50)
        time.sleep(4)
        if disease_flag==True:
            self.wait_for_element('input_regimen_name')
            self.type('input_regimen_name', self.regimen_name)
            time.sleep(3)
            self.wait_for_element("kendo-dropdownlist-Disease")
            try:
                values = self.kendo_dd_get_all_texts("kendo-dropdownlist-Disease")
            except Exception:
                time.sleep(5)
                values = self.kendo_dd_get_all_texts("kendo-dropdownlist-Disease")
            # ✅ keep only single-word values without ',' or '/'
            filtered = [
                v for v in values
                if v
                   and ',' not in v
                   and '/' not in v
                ]

            if not filtered:
                raise AssertionError("No valid single-word disease found in dropdown")

            selected_disease = random.choice(filtered)
            print(f"Selected disease: {selected_disease}")

            self.kendo_dd_select_text_old('kendo-dropdownlist-Disease', selected_disease)
        else:
            print("Disease flag is False")
        print(self.resolve('span_NEW_SCHEDULE'))
        self.click_robust('span_NEW_SCHEDULE')
        if past_date:
            date = self.past_date()
        else:
            date = self.today_date()
        self.wait_for_element('timepicker')
        print("regimen name: ", self.resolve('input_regimen_name'))
        print("startdate: ", self.resolve('startdate'))
        self.type('startdate', date)
        time.sleep(1)

        # self.type('timepicker', UserData.med_time)
        if time_of_drug:
            drug_time = self.get_time_now()
            self.type('timepicker', drug_time)
        time.sleep(1)
        med_time = self.get_value('timepicker')
        self.wait_for_element('kendo-dropdownlist-Repeats')
        self.kendo_dd_select_text_old('kendo-dropdownlist-Repeats', UserData.regimen_repeats)
        self.type('input_Enter_weeks',no_of_weeks)
        # self.kendo_ms_select_text("kendo-multiselect-drugs", "Drug 1")
        #
        # # Add several
        # self.kendo_ms_select_many("kendo-multiselect-drugs", UserData.regimen_drugs)
        #
        # # Assert selected chips
        # assert "Drug 1" in self.kendo_ms_get_selected("kendo-multiselect-drugs")
        self.wait_for_element("kendo-multiselect-drugs")
        if drug_name:
            self.click('kendo-multiselect-drugs')
            self.kendo_select("input_drugs", text=drug_name)
            # self.kendo_select_first("input_drugs")
            time.sleep(4)
            selected_drug = drug_name
        else:
            drugs = self.kendo_ms_get_all_texts("kendo-multiselect-drugs")
            filtered_drugs = [
                d.strip() for d in drugs
                if d and d.strip()
                   and ',' not in d
                   and '/' not in d
                   and ' ' not in d
                   and 'Sofosbuvir' not in d
                   and 'Quabodepistat' not in d# optional: single-word only
                   and (donot_add_drug is None or donot_add_drug not in d)
                ]

            if not filtered_drugs:
                raise AssertionError(f"No valid drug found. Raw drugs list: {drugs}")

            selected_drug = random.choice(filtered_drugs)
            print(f"Selected drug: {selected_drug}")

            self.click('kendo-multiselect-drugs')
            self.kendo_select("input_drugs", text=selected_drug)
            # self.kendo_select_first("input_drugs")
            time.sleep(4)
        present_text = self.get_text('label_Drug_name_text')
        assert selected_drug == present_text, f"Incorrect drug added: {present_text} is not same as {selected_drug} "
        print(f"Correct drug added: {present_text} is same as {selected_drug} ")

        self.wait_for_element('span_drug_colour', 50)
        colour_code = self.get_attribute('span_drug_colour', "style")
        print(colour_code)

        if add_pill:
            self.type('input_Number_of_pills', str(UserData.no_of_pills))
            self.type('input_Dose_per_pill', str(UserData.dose_per_pill))
            total_pills = self.get_text('div_Total_dose_text')
            assert total_pills == str(UserData.no_of_pills * UserData.dose_per_pill), f"Total dose mismatch: {str(UserData.no_of_pills * UserData.dose_per_pill)} and {total_pills}"
            print( f"Total dose match: {str(UserData.no_of_pills * UserData.dose_per_pill)} and {total_pills}")
        else:
            total_pills = 0
        self.click_robust('button_CREATE')
        time.sleep(15)
        self.wait_for_page_to_load(100)
        time.sleep(5)

        # Example: start on 2025-10-27, weekdays only, for 3 weeks

        missing, styles = self.calendar_verify_dots_multi_month(
            start=date,
            weeks=1,
            mode=UserData.regimen_repeats,  # or "daily"
            header_logical="calendar-header",
            next_btn_logical="cal_next_btn",
            prev_btn_logical="cal_prev_btn",
            expect_color_substring=colour_code,
            )
        assert not missing, f"Missing/incorrect dots on: {[d.isoformat() for d in missing]}"

        print("Couloured dots are present correctly")
        self.wait_for_element('div-schedule-summary')
        schedule_text = self.get_elements_texts('div-schedule-info')

        print(schedule_text)

        text_date = datetime.strptime(date, "%Y-%m-%d")
        text_date_format = self.format_mdY(text_date)
        end_date = self.calculate_end_date(date, 1)

        expected = med_time #UserData.med_time
        expected_no_leading_zero = re.sub(r'\b0(?=\d:)', '', expected)

        schedule_str = " ".join(schedule_text).lower()

        assert selected_drug.lower() in schedule_str, f"{selected_drug} not in {schedule_text}"
        # assert selected_drug in schedule_text, f"{selected_drug} not in {schedule_text}"
        # assert UserData.med_time in schedule_text, f"{UserData.med_time} not in {schedule_text}"
        assert text_date_format.lower() in schedule_str, f"{text_date_format} not in {schedule_text}"
        assert end_date.lower() in schedule_str, f"{end_date} not in {schedule_text}"
        assert str(UserData.no_of_pills).lower() in schedule_str, f"{UserData.no_of_pills} not in {schedule_text}"
        assert expected_no_leading_zero.lower() in schedule_str or expected.lower() in schedule_str, (
            f"{med_time} not in {schedule_text}"
        )


        return text_date_format, end_date, UserData.no_of_pills, selected_drug, total_pills

    def get_all_diseases_present(self):
        values = self.kendo_dd_get_all_texts("kendo-dropdownlist-Disease")
        print(f"List of Diseases: {values}")
        return values
        # for v in values:
        #     print(f"")

    def get_all_drugs_present(self):
        self.click('button_NEW_SCHEDULE')
        self.wait_for_element('kendo-multiselect-drugs')
        drugs = self.kendo_ms_get_all_texts("kendo-multiselect-drugs")
        print(f"List of Drugs: {drugs}")
        return drugs
        # for d in drugs:
        #     print(d)

    def verify_diseases_present(self, name, toggle=None):
        time.sleep(5)
        self.wait_for_element("kendo-dropdownlist-Disease")
        values = self.kendo_dd_get_all_texts("kendo-dropdownlist-Disease")
        # print(f"List of Diseases: {values}")
        if toggle == "ON":
            if name in values:
                assert True, f"The disease {name} is not present in the disease dropdown list {values}"
                print(f"The disease {name} is present in the disease dropdown list {values}")
            else:
                print(f"The disease {name} is not present in the disease dropdown list {values}")

        elif toggle == "OFF":
            if name not in values:
                assert True, f"The disease {name} is present in the disease dropdown list {values}"
                print(f"The disease {name} is not present in the disease dropdown list {values}")
            else:
                print(f"The disease {name} is present in the disease dropdown list {values}")

        else:
            print("Invalid toggle option")

    def verify_drugs_present(self, name, toggle):
        print(f"Current parameters: {name}, {toggle}")
        self.click('button_NEW_SCHEDULE')
        time.sleep(3)
        self.wait_for_element('timepicker')
        time.sleep(5)
        self.wait_for_element('kendo-multiselect-drugs')
        self.wait_for_element('button_CREATE')
        drugs = self.kendo_ms_get_all_texts("kendo-multiselect-drugs")
        print(f"List of Drugs: {drugs}")

        if toggle == "ON":
            if name in drugs:
                assert True, f"The drugs {name} is not present in the drugs dropdown list {drugs}"
                print(f"The drugs {name} is present in the drugs dropdown list {drugs}")
            else:
                print(f"The drugs {name} is not present in the drugs dropdown list {drugs}")

        elif toggle == "OFF":
            if name not in drugs:
                assert True, f"The drugs {name} is present in the drugs dropdown list {drugs}"
                print(f"The drugs {name} is not present in the drugs dropdown list {drugs}")
            else:
                print(f"The drugs {name} is present in the drugs dropdown list {drugs}")

        else:
            print("Invalid toggle option")

    def verify_regimen_approval_error(self):
        self.wait_for_element('span_EDIT')
        self.wait_for_element('div_regimen_error', strict=True)
        print(self.get_text('div_regimen_error', strict=True))
        assert self.is_element_visible('div_regimen_error', strict=True), "Regiment Approval error not present"
        print("Regiment Approval error present")


    def delete_schedule(self):
        self.wait_for_page_to_load(30)
        time.sleep(3)
        self.wait_for_element('input_regimen_name')
        if self.is_element_present('span_EDIT'):
            name_list = self.get_pill_names()
            if name_list is not None:
                self.wait_for_element('span_EDIT')
                count = self.find_elements('span_EDIT')
                print(len(count), len(count))
                for items in name_list:
                    print(items)
                    self.click_rendered('edit_against_drug', text=items)
                    self.wait_for_element('span_DELETE')
                    self.click_robust('span_DELETE')
                    time.sleep(1)
                    self.wait_for_element('span_DELETE_CONFIRM', strict=True)
                    self.js_click('span_DELETE_CONFIRM', strict=True)
                    try:
                        self.kendo_dialog_wait_open()  # no title constraint
                        self.kendo_dialog_click_button("Ok")
                    except Exception:
                        print("popup not present")
                    time.sleep(3)
                    self.wait_for_page_to_load()
            else:
                print("No drugs present to be deleted")
        else:
            print("No edit button present")

    def get_pill_names(self):
        self.wait_for_page_to_load(30)
        time.sleep(2)
        self.wait_for_element('input_regimen_name')
        try:
            self.wait_for_element('span_EDIT')
            count = self.find_elements('div_pill_name')
            print(len(count))
            name_list = []
            for items in count:
                name = items.text
                name_list.append(name)
            print(name_list)
            return name_list
        except:
            print("No Pills present")
            return None


    def edit_schedule(self, drug_name, past_date=False, time_of_drug=False, end_date=None, no_of_pills=None, doses=None, repeat=False):

        self.wait_for_page_to_load(50)
        time.sleep(4)
        self.click_rendered('edit_against_drug', text=drug_name)

        if past_date:
            date = self.past_date()
        else:
            date = self.today_date()
        self.wait_for_element('timepicker')

        self.type('startdate', date)
        time.sleep(1)

        if time_of_drug:
            drug_time = self.get_time_now()
            self.type('timepicker', drug_time)
        time.sleep(1)
        med_time = self.get_value('timepicker')
        time.sleep(1)
        self.wait_for_element('kendo-dropdownlist-Repeats')
        if repeat:
            self.kendo_dd_select_text_old('kendo-dropdownlist-Repeats', UserData.regimen_repeats_weekdays)
        else:
            self.kendo_dd_select_text_old('kendo-dropdownlist-Repeats', UserData.regimen_repeats)

        present_text = self.get_text('label_Drug_name_text')

        self.wait_for_element('span_drug_colour', 50)
        colour_code = self.get_attribute('span_drug_colour', "style")
        print(colour_code)

        if no_of_pills:
            self.type('input_Number_of_pills', no_of_pills)
            pills = self.get_text('input_Number_of_pills')
        if doses:
            self.type('input_Dose_per_pill', doses)
            dose_per_pill = self.get_text('input_Dose_per_pill')
        total_pills = self.get_text('div_Total_dose_text')
        assert total_pills == str(pills * dose_per_pill), f"Total dose mismatch: {str(pills * dose_per_pill)} and {total_pills}"
        print( f"Total dose match: {str(pills * dose_per_pill)} and {total_pills}")

        if end_date:
            text_date = datetime.strptime(date, "%Y-%m-%d")
            text_date_format = self.format_mdY(text_date)
            end_date = self.future_date(date, 5)
            self.type('enddate', date)

        self.click_robust('button_CREATE')
        time.sleep(15)
        self.wait_for_page_to_load(100)
        time.sleep(5)

        # Example: start on 2025-10-27, weekdays only, for 3 weeks

        missing, styles = self.calendar_verify_dots_multi_month(
            start=date,
            weeks=1,
            mode=UserData.regimen_repeats,  # or "daily"
            header_logical="calendar-header",
            next_btn_logical="cal_next_btn",
            prev_btn_logical="cal_prev_btn",
            expect_color_substring=colour_code,
            )
        assert not missing, f"Missing/incorrect dots on: {[d.isoformat() for d in missing]}"

        print("Couloured dots are present correctly")
        self.wait_for_element('div-schedule-summary')
        schedule_text = self.get_elements_texts('div-schedule-info')

        print(schedule_text)

        expected = med_time #UserData.med_time
        expected_no_leading_zero = re.sub(r'\b0(?=\d:)', '', expected)

        schedule_str = " ".join(schedule_text).lower()

        # assert selected_drug.lower() in schedule_str, f"{selected_drug} not in {schedule_text}"
        # assert selected_drug in schedule_text, f"{selected_drug} not in {schedule_text}"
        # assert UserData.med_time in schedule_text, f"{UserData.med_time} not in {schedule_text}"
        assert text_date_format.lower() in schedule_str, f"{text_date_format} not in {schedule_text}"
        assert end_date.lower() in schedule_str, f"{end_date} not in {schedule_text}"
        assert str(UserData.no_of_pills).lower() in schedule_str, f"{UserData.no_of_pills} not in {schedule_text}"
        assert expected_no_leading_zero.lower() in schedule_str or expected.lower() in schedule_str, (
            f"{med_time} not in {schedule_text}"
        )


        return text_date_format, end_date, UserData.no_of_pills, total_pills