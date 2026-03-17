import random
import time
from datetime import date, datetime

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string, fetch_random_digit
from user_inputs.user_data import UserData


class PatientOverviewPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)


    def open_patient_overview_page(self):
        self.click('k-tabstrip-tab-Overview')
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
        except Exception:
            print("popup not present")

    def verify_patient_overview_page(self):
        time.sleep(5)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
        except Exception:
            print("popup not present")
        self.wait_for_page_to_load()
        self.wait_for_element('k-opened-tabstrip-tab')
        self.unheal_all('k-opened-tabstrip-tab')
        time.sleep(3)
        tabname = self.get_text('k-opened-tabstrip-tab')
        print(tabname)
        assert tabname == "Overview", "Overview tab is not opened"
        print("Opened tab is Overview")

    def days_completed(self, start_date_str: str) -> int:
        # Parse the input string like "Sep 12, 2025"
        start_date = datetime.strptime(start_date_str, "%b %d, %Y").date()
        today = datetime.today().date()

        # Difference in days + 1 (to count the start day as day 1)
        diff = (today - start_date).days + 1

        # If the start date is in the future, return 0
        return diff

    def check_calendar_and_doses(self, formatted_now, review_text, med_name, start_date, total_dose):
        taken_doses = self.days_completed(start_date)
        left_doses = int(total_dose)-int(taken_doses)
        print(f"Total pills: {total_dose}, Taken doses: {taken_doses}, Left Doses: {left_doses}")

        self.wait_for_element('span_cal_today_date')

        date_value = self.get_text('span_cal_today_date', strict=True)
        today_date = date.today()
        assert date_value.strip() == str(today_date.day), f"{date_value.strip()} not matching current date {str(today_date.day)}"
        print(f"{date_value.strip()} matching current date {str(today_date.day)}")
        dose_status = self.get_attribute('div_cal_today_dose_schedule', 'class', strict=True)
        print(dose_status)
        assert "taken-dose-icon" == dose_status, f"taken-dose-icon not matching current status {dose_status}"
        print(f"taken-dose-icon matching current status {dose_status}")
        print(self.get_attribute('span_cal_today_video_status', 'class', strict=True))
        assert self.is_element_present('span_cal_today_video_status', strict=True, timeout=20), f"video icon not present"
        print("video icon is present")

        drug_name = self.get_text('td_drug_name')
        drug_taken = self.get_text('td_drug_taken')
        drug_left = self.get_text('td_drug_left')
        drug_scheduled = self.get_text('td_drug_scheduled')

        print(drug_name, drug_scheduled, drug_taken, drug_left)
        assert drug_name == med_name, f"{drug_name} not matching {med_name}"
        assert str(drug_taken) == str(taken_doses), f"{drug_taken} not matching {taken_doses}"
        assert str(drug_left) == str(left_doses), f"{drug_left} not matching {left_doses}"
        assert str(drug_scheduled) == str(total_dose), f"{drug_scheduled} not matching {total_dose}"

        print("All drug details are correctly displayed.")


    def check_calendar_presence(self):
        self.wait_for_element('div_calendar')
        assert self.is_element_visible('div_calendar'), "Calender is not present"
        print("Calender is present")

    def check_doses_table_before(self):
        self.wait_for_element('div_calendar')
        assert self.is_element_visible('div_calendar'), "Calender is not present"
        print("Calender is present")

        assert self.is_element_present('towards_adherence_td_drug_name', strict=True), "Counts towards adherence row not present"
        print("Counts towards adherence row present")
        assert self.is_element_present('not_towards_adherence_td_drug_name', strict=True), "does not count towards adherence row not present"
        print("Does not count towards adherence row present")

        assert self.is_element_present('td_drug_no_records', strict=True), "No records available not present"
        print("No records available present")

        for item in UserData.overview_doses_table_columns:
            adherence = self.get_text(f"towards_adherence_td_drug_{item}").strip()
            not_adherence = self.get_text(f"not_towards_adherence_td_drug_{item}").strip()
            assert 0 == int(adherence), f"towards_adherence_td_drug_{item} value {adherence} does not match 0"
            print( f"towards_adherence_td_drug_{item} value {adherence} match 0")
            assert 0 == int(not_adherence), f"not_towards_adherence_td_drug_{item} value {not_adherence} does not match 0"
            print(f"not_towards_adherence_td_drug_{item} value {not_adherence} match 0")

