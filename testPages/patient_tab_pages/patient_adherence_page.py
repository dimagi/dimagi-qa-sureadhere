import random
import time
from datetime import date, datetime

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
            self.kendo_dialog_click_button("Ok")
        except Exception:
            print("popup not present")
        self.wait_for_page_to_load()
        self.wait_for_element('k-opened-tabstrip-tab')
        self.unheal_all('k-opened-tabstrip-tab')
        time.sleep(3)
        tabname = self.get_text('k-opened-tabstrip-tab')
        print(tabname)
        assert tabname == "Adherence", "Adherence tab is not opened"
        print("Opened tab is Adherence")

    def verify_regimen_name_presence(self, name):
        assert self.is_element_present_rendered('span_regimen_name', text=name), f"{name} is not present"
        print(f"{name} is present")

    def verify_patient_adherence_page(self):
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
        assert tabname == "Adherence", "Adherence tab is not opened"
        print("Opened tab is Adherence")

    def verify_patient_adherence_dose_status(self, status, flag=True):
        text = self.kendo_dd_get_selected_text('doseStatus')
        if flag == True:
            assert str(text).strip() == status, f"{status} is not selected"
            print(f"{status} is selected")
            return True
        else:
            assert not str(text).strip() == status, f"{status} is selected"
            print(f"{status} is not selected")
            return False

    def verify_patient_adherence_dose_saved_status(self, status, flag=True):
        text = self.kendo_dd_get_selected_text('kendo-dropdown-saved_status')
        if flag == True:
            assert str(text).strip() == status, f"{status} is not selected"
            print(f"{status} is selected")
            return True
        else:
            assert not str(text).strip() == status, f"{status} is selected"
            print(f"{status} is not selected")
            return False

    def set_patient_adherence_dose_status(self, status):
        self.kendo_dd_select_text_old('doseStatus', status)
        text = self.kendo_dd_get_selected_text('doseStatus')
        assert str(text).strip() == status, f"{status} is not selected"
        print(f"{status} is selected")

    def set_patient_adherence_saved_status(self, status):
        self.kendo_dd_select_text_old('kendo-dropdown-saved_status', status)
        text = self.kendo_dd_get_selected_text('kendo-dropdown-saved_status')
        assert str(text).strip() == status, f"{status} is not selected"
        print(f"{status} is selected")

    def submit_changes(self):
        self.click_robust('span_SUBMIT_REVIEW')
        time.sleep(2)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
            self.wait_for_overlays_to_clear(5)
        except Exception:
            print("popup not present after save")
        time.sleep(5)

    def check_calendar_and_comment_for_adherence(self, now, formatted_now, review_text):
        self.wait_for_element('span_cal_today_date')
        self.click('span_cal_today_date' , strict=True)
        date_value = self.get_text('span_cal_today_date', strict=True)
        today_date = date.today()
        assert date_value.strip() == str(today_date.day), f"{date_value.strip()} not matching current date {str(today_date.day)}"
        print(f"{date_value.strip()} matching current date {str(today_date.day)}")
        dose_status = self.get_attribute('div_cal_today_dose_schedule', 'class')
        print(dose_status)
        assert "taken-dose-icon" == dose_status or "open-dose-icon" == dose_status, f"taken-dose-icon/open-dose-icon not matching current status {dose_status}"
        print(f"taken-dose-icon/open-dose-icon matching current status {dose_status}")
        assert self.is_element_present('span_cal_today_video_status', strict=True), f"video icon not present"
        print("video icon is present")
        timestamp_text = self.get_text_rendered('span_commented_timestamp', text=review_text)
        self.assert_timestamp_within_minutes(timestamp_text, now, tolerance_minutes=2)
        # assert formatted_now in timestamp_text, f"{str(formatted_now)} not in {timestamp_text}"
        print(f"{str(formatted_now)} is in {timestamp_text}")

        full_text = self.get_text_rendered('div_commented_user_timestamp', text=review_text)
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

    def verify_side_effect(self, side_effect):
        side_effect_text = self.get_text('li_current-side-effects', strict=True)
        print(side_effect_text.strip())
        side_effect_text = side_effect_text.replace("x", "")
        side_effect_text = side_effect_text.strip()
        assert side_effect in side_effect_text.strip(), f"{side_effect} is not in {side_effect_text.strip()}"
        print(f"selected side effect is {side_effect_text}")

    def verify_selected_date(self, date_selected):
        value = self.get_text('div_selected_date', strict=True)
        print(value)
        assert str(value) == str(date_selected), f"{value} did not match {date_selected}"
        print(f"{value} matched {date_selected}")

    def add_dose_status(self, status):
        self.kendo_dd_select_text_old("kendo-dropdown-saved_status", status)
        text = self.kendo_dd_get_selected_text('kendo-dropdown-saved_status')
        assert str(text).strip() == status, f"{status} is not selected"
        print(f"{status} is selected")
        self.wait_for_element('edit_doses')
        self.click('edit_doses', strict=True)
        drug_date, drug_time = self.get_time_now()
        ate_value = "Yes"
        obs_method = "VDOT (recorded)"
        self.type('set_time', drug_time, strict=True)
        try:
            self.type('last_meal_time', drug_time, strict=True)
            self.type('last_meal_date', drug_date, strict=True)
        except:
            print("Last meal time and date fields not present")
        try:
            self.kendo_dd_select_text_old('kendo-dropdownlist-ate_in_last_hour', ate_value)
        except:
            print("Ate in last hour field not present")
        self.kendo_dd_select_text_old("kendo-dropdownlist-observation_method", obs_method)
        return drug_time, obs_method

    def verify_dose_summary(self, drug_time, obs_method):
        assert self.is_element_present('edit_doses')
        print(drug_time, obs_method)
        drug_time = self.format_hMp(drug_time)
        assert self.get_text('span_Dose time').strip() ==drug_time, f"{self.get_text('span_Dose time')} not matching {drug_time}"
        assert self.get_text('span_Ate in the last hour').strip() =="Yes", f"{self.get_text('span_Ate in the last hour')} not matching Yes"
        assert self.get_text('span_Observation method').strip() ==obs_method, f"{self.get_text('span_Observation method')} not matching {obs_method}"
        print("Dose summary verified")

    def verify_auto_filled_tag(self):
        assert self.is_element_present("auto_filled_tag", strict=True, timeout=15), "auto-filled tag is not present"
        print("auto-filled tag is present")

    def get_time_now(self):
        now = datetime.now()
        time_now = now.time().strftime("%I:%M %p")
        date_now = now.strftime("%b %d, %Y").replace(" 0"," ")
        print(time_now)
        print(date_now)
        return date_now, time_now

    def open_video_form(self):
        self.wait_for_element('div_video-icon')
        self.click('div_video-icon')

    def check_video_link_checkbox(self):
        self.wait_for_element('span_All')
        self.click('span_All')
        time.sleep(3)
        self.wait_for_element("input_eventIsLinked_chb_0")
        self.click('input_eventIsLinked_chb_0', strict=True)
        time.sleep(3)
        self.submit_changes()

    def add_comment(self, text):
        review_text = "Meds taken, Review Approved with FF ON"
        self.type_and_trigger('newCommentInput', review_text, strict=True)
        self.unheal_all('span_Comment')
        self.unheal('span_Comment')
        self.wait_for_element('span_Comment')
        self.click('span_Comment', strict=True)
        time.sleep(2)
        return review_text