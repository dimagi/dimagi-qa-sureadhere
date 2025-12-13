import random
import time
from datetime import date

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string, fetch_random_digit
from user_inputs.user_data import UserData


class PatientAdherencePage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def open_patient_adherence_page(self):
        self.click('k-tabstrip-tab-Adherence')
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Continue")
        except Exception:
            print("popup not present")

    def verify_patient_adherence_page(self):
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element('k-opened-tabstrip-tab')
        tabname = self.get_text('k-opened-tabstrip-tab')
        assert tabname == "Adherence", "Adherence tab is not opened"
        print("Opened tab is Adherence")

    def check_calendar_and_comment_for_adherence(self, formatted_now, review_text):
        self.wait_for_element('span_cal_today_date')
        self.click('span_cal_today_date' , strict=True)
        date_value = self.get_text('span_cal_today_date', strict=True)
        today_date = date.today()
        assert date_value.strip() == str(today_date.day), f"{date_value.strip()} not matching current date {str(today_date.day)}"
        print(f"{date_value.strip()} matching current date {str(today_date.day)}")
        dose_status = self.get_attribute('div_cal_today_dose_schedule', 'class')
        print(dose_status)
        assert "taken-dose-icon" == dose_status, f"taken-dose-icon not matching current status {dose_status}"
        print(f"taken-dose-icon matching current status {dose_status}")
        assert self.is_element_present('span_cal_today_video_status', strict=True), f"video icon not present"
        print("video icon is present")
        timestamp_text = self.get_text('span_commented_timestamp')
        assert formatted_now in timestamp_text, f"{str(formatted_now)} not in {timestamp_text}"
        print(f"{str(formatted_now)} is in {timestamp_text}")

        full_text = self.get_text('div_commented_user_timestamp')
        assert review_text in full_text, f"{review_text} not in {full_text}"
        print(f"{review_text} is in {full_text}")

    def fillup_side_effects(self):
        self.click('span_cal_today_date')
        time.sleep(2)
        self.wait_for_element('kendo-dropdown-saved_status')
        self.wait_for_element('doseStatus')
        self.wait_for_element('providerObservation')
        self.wait_for_element('span_SUBMIT_REVIEW')

        self.kendo_dd_select_text_old('kendo-dropdown-saved_status', UserData.med_status)
        saved_status = self.kendo_dd_get_selected_text(logical_name="kendo-dropdown-saved_status")
        print(f"Selected status is {saved_status}")
        self.kendo_dd_select_text_old('doseStatus', UserData.med_status)
        dose_status = self.kendo_dd_get_selected_text(logical_name="doseStatus")
        print(f"Dose status is {dose_status}")
        selected_side_effect = random.choice(UserData.side_effect)
        print(selected_side_effect)
        self.kendo_dd_select_text_old('providerObservation', UserData.provider_observation)
        provider_observation = self.kendo_dd_get_selected_text(logical_name="providerObservation")
        print(f"Provider Observation is {provider_observation}")

        self.kendo_autocomplete_select("input-side_effects", "a", select_first=True)
        time.sleep(1)
        self.wait_for_element('li_current-side-effects')
        side_effect_text = self.get_text('li_current-side-effects')
        print(side_effect_text.strip())
        side_effect_text = side_effect_text.replace("x", "")
        side_effect_text = side_effect_text.strip()
        # assert selected_side_effect in side_effect_text.strip(), f"{selected_side_effect} is not in {side_effect_text.strip()}"
        print(f"selected side effect is {side_effect_text}")


        self.click_robust('span_SUBMIT_REVIEW')
        time.sleep(2)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
            self.wait_for_overlays_to_clear(5)
        except Exception:
            print("popup not present after save")
        time.sleep(5)
        self.refresh()
        time.sleep(10)
        self.verify_patient_adherence_page()
        self.wait_for_element('span_cal_today_date')
        assert self.is_element_visible('span_cal_today_symptoms'), "side effects not updated in calendar"
        print("side effects updated in calendar")


        return side_effect_text

    def open_video_event(self):
        self.click('div_event_item')