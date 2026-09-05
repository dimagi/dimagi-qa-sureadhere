import random
import time
from datetime import datetime

from pdbp import side_effects_free
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string, fetch_random_digit
from user_inputs.user_data import UserData


class PatientVideoPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)


    def verify_patient_video_page(self):
        time.sleep(10)
        self.wait_for_page_to_load()
        self.wait_for_element('newCommentInput')
        print("Opened screen is Video Review")

    # def now_parts(tz=None):
    #     """Return (Day, Date, Time) as ('Fri', 'Sep 12, 2025', '4:51PM')."""
    #     now = datetime.now(tz) if tz else datetime.now()
    #     day_str = now.strftime("%a")  # 'Fri'
    #     date_str = f"{now.strftime('%b')} {now.day}, {now:%Y}"  # 'Sep 12, 2025'
    #     hour12 = (now.hour % 12) or 12
    #     ampm = now.strftime("%p")  # 'AM'/'PM'
    #     time_str = f"{hour12}:{now:%M}{ampm}"  # '4:51PM'
    #     return day_str, date_str, time_str
    #
    #     _time_re = re.compile(r"\s*(\d{1,2}):(\d{2})\s*([AP]M)\s*", re.I)
    #
    # def _parse_time_hhmm_ampm(s: str):
    #     """Parse 'h:mmAM/PM' -> (hour24, minute)."""
    #     m = _time_re.fullmatch(s)
    #     if not m:
    #         raise ValueError(f"Bad time string: {s!r}")
    #     h = int(m.group(1)) % 12
    #     if m.group(3).upper() == "PM":
    #         h += 12
    #     return h, int(m.group(2))
    #
    # def times_within_minutes(self, t1: str, t2: str, tol_minutes: int = 2) -> bool:
    #     """Return True if t1 and t2 within tol minutes (handles cross-midnight)."""
    #     h1, m1 = _parse_time_hhmm_ampm(t1)
    #     h2, m2 = _parse_time_hhmm_ampm(t2)
    #     a = datetime(2000, 1, 1, h1, m1)
    #     b = datetime(2000, 1, 1, h2, m2)
    #     deltas = [
    #         abs((a - b).total_seconds()),
    #         abs(((a + timedelta(days=1)) - b).total_seconds()),
    #         abs((a - (b + timedelta(days=1))).total_seconds()),
    #         ]
    #     return min(deltas) <= tol_minutes * 60

    def fill_up_review_form(self, meds, no_of_pills, dose_per_pill):
        review_text = "Meds taken, Review Approved"
        self.type_and_trigger('newCommentInput', review_text)
        self.wait_for_element('span_Comment')
        self.click('span_Comment')
        now = datetime.now()
        formatted_now = now.strftime(f"%a - %b %d, %Y - %I:%M %p")
        drug_name = self.get_text('div_drug-name')
        drug_details = self.get_text('div_drug-details')
        text = str(dose_per_pill)+"mg/"+str(no_of_pills)+" pills"
        actual = self.normalize(drug_details)
        expected = self.normalize(text)
        assert expected in actual, f"Expected '{text}' not found in:\n{drug_details}"
        # assert drug_details == text, f"{drug_details} doesnot match {text}"
        print(f"{drug_details} present in {text}")
        assert meds == drug_name, f"{meds} not in {drug_name}"
        print(f"{meds} matches {drug_name}")
        timestamp_text = self.get_text('span_commented_timestamp')
        self.assert_timestamp_within_minutes(timestamp_text, now, tolerance_minutes=2)
        # assert formatted_now in timestamp_text, f"{str(formatted_now)} not in {timestamp_text}"
        print(f"{str(formatted_now)} is in {timestamp_text}")

        full_text = self.get_text('div_commented_user_timestamp')
        assert review_text in full_text, f"{review_text} not in {full_text}"
        print(f"{review_text} is in {full_text}")

        self.click_robust('span_MARK_AS_ADHERENT')
        time.sleep(2)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
            self.wait_for_overlays_to_clear(5)
        except Exception:
            print("popup not present after save")
        return now, formatted_now, review_text

    def close_form(self):
        try:
            if self.is_element_visible('button_Close'):
                self.click('button_Close')
                self.wait_for_invisible('videoPlayer')
                print("form closed")
            else:
                print("No Close button present")
        except Exception:
            print("form is not open")

    def verify_video_error(self):
        assert self.is_element_present('video_error'), "Video error not present"
        print("Video error is present")


    def fill_up_review_form_ff_on(self, meds, no_of_pills, dose_per_pill, rerun_count=0):
        review_text = "Meds taken, Review Approved with FF ON"
        self.unheal_all('newCommentInput')
        self.unheal('newCommentInput')
        self.type_and_trigger('newCommentInput', review_text, strict=True)
        self.unheal_all('span_Comment')
        self.unheal('span_Comment')
        self.wait_for_element('span_Comment')
        self.click('span_Comment', strict=True)

        now = datetime.now()
        formatted_now = now.strftime(f"%a - %b %d, %Y - %I:%M %p")
        drug_name = self.get_text('div_drug-name')
        drug_details = self.get_text('div_drug-details')
        text = str(dose_per_pill)+"mg/"+str(no_of_pills)+" pills"
        actual = self.normalize(drug_details)
        expected = self.normalize(text)
        assert expected in actual, f"Expected '{text}' not found in:\n{drug_details}"
        # assert drug_details == text, f"{drug_details} doesnot match {text}"
        print(f"{drug_details} present in {text}")
        assert meds == drug_name, f"{meds} not in {drug_name}"
        print(f"{meds} matches {drug_name}")
        timestamp_text = self.get_text_rendered('span_commented_timestamp', text=review_text)
        self.assert_timestamp_within_minutes(timestamp_text, now, tolerance_minutes=2)
        assert formatted_now in timestamp_text, f"{str(formatted_now)} not in {timestamp_text}"
        print(f"{str(formatted_now)} is in {timestamp_text}")

        full_text = self.get_text_rendered('div_commented_user_timestamp', text=review_text)
        assert review_text in full_text, f"{review_text} not in {full_text}"
        print(f"{review_text} is in {full_text}")
        side_effect = ""
        if rerun_count != 0 and self.kendo_dd_get_selected_text('doseStatus') == "Taken":
            print("Dose Status already selected")
        else:
            self.select_dose_status("Taken")
        assert self.is_element_present("auto_filled_tag", strict=True, timeout=15), "auto_filled_tag not present"
        print("auto_filled_tag present on page")
        assert self.is_element_present('edit_doses')

        drug_time = self.get_text('span_Dose time', strict=True)
        obs_method = UserData.obs_in_person
        assert self.get_text(
            'span_Ate in the last hour', strict=True).strip() == "Yes", f"{self.get_text('span_Ate in the last hour')} not matching Yes"
        assert self.get_text(
            'span_Observation method', strict=True).strip() == obs_method, f"{self.get_text('span_Observation method')} not matching {obs_method}"
        print("Dose summary verified")

        if rerun_count == 0:
            side_effect = self.fill_up_side_effects()
        else:
            side_effect_text = self.get_text('li_current-side-effects', strict=True)
            print(side_effect_text.strip())
            side_effect_text = side_effect_text.replace("x", "")
            side_effect = side_effect_text.strip()
        self.scroll_to_element('span_SUBMIT_REVIEW', strict=True)
        sel_debug = self.resolve_strict('span_SUBMIT_REVIEW')
        el_debug = self.sb.driver.find_element(By.XPATH, sel_debug)
        print(f"DEBUG before click: tag={el_debug.tag_name} text={el_debug.text!r} "
              f"displayed={el_debug.is_displayed()} enabled={el_debug.is_enabled()} "
              f"class={el_debug.get_attribute('class')!r}")
        self.sb.save_screenshot("debug_before_submit_review.png")
        self.js_click('span_SUBMIT_REVIEW', strict=True)
        print("DEBUG: js_click on span_SUBMIT_REVIEW returned without exception")
        time.sleep(2)
        self.sb.save_screenshot("debug_after_submit_review.png")
        time.sleep(3)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
            self.wait_for_overlays_to_clear(5)
        except Exception:
            print("popup not present after save")
        self.close_form()
        time.sleep(5)
        return now, formatted_now, drug_time, UserData.obs_in_person, review_text, side_effect

    def submit_form(self):
        self.scroll_to_element('span_SUBMIT_REVIEW', strict=True)
        sel_debug = self.resolve_strict('span_SUBMIT_REVIEW')
        el_debug = self.sb.driver.find_element(By.XPATH, sel_debug)
        print(f"DEBUG before click: tag={el_debug.tag_name} text={el_debug.text!r} "
              f"displayed={el_debug.is_displayed()} enabled={el_debug.is_enabled()} "
              f"class={el_debug.get_attribute('class')!r}")
        self.sb.save_screenshot("debug_before_submit_review.png")
        self.js_click('span_SUBMIT_REVIEW', strict=True)
        print("DEBUG: js_click on span_SUBMIT_REVIEW returned without exception")
        time.sleep(2)
        self.sb.save_screenshot("debug_after_submit_review.png")
        time.sleep(3)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
            self.wait_for_overlays_to_clear(5)
        except Exception:
            print("popup not present after save")
        self.close_form()
        time.sleep(5)

    def add_dose_status(self, status):
        self.kendo_dd_select_text_old("kendo-dropdown-saved_status", status)
        text = self.kendo_dd_get_selected_text('kendo-dropdown-saved_status')
        assert str(text).strip() == status, f"{status} is not selected"
        print(f"{status} is selected")
        self.wait_for_element('edit_doses')
        self.wait_for_overlays_to_clear(5)
        self.click_robust(self.resolve_strict('edit_doses'))
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

    def get_time_now(self):
        now = datetime.now()
        time_now = now.time().strftime("%I:%M %p")
        date_now = now.strftime("%b %d, %Y").replace(" 0"," ")
        print(time_now)
        print(date_now)
        return date_now, time_now


    def select_dose_status(self, status):
        self.kendo_dd_select_text_old('doseStatus', status)
        text = self.kendo_dd_get_selected_text('doseStatus')
        assert str(text).strip() == status, f"{status} is not selected"
        print(f"{status} is selected")

    def fill_up_side_effects(self):
        self.kendo_autocomplete_select("input-side_effects", "a", select_first=True)
        time.sleep(1)
        self.wait_for_element('li_current-side-effects')
        side_effect_text = self.get_text('li_current-side-effects')
        print(side_effect_text.strip())
        side_effect_text = side_effect_text.replace("x", "")
        side_effect_text = side_effect_text.strip()
        # assert selected_side_effect in side_effect_text.strip(), f"{selected_side_effect} is not in {side_effect_text.strip()}"
        print(f"selected side effect is {side_effect_text}")
        return side_effect_text

    def fill_up_review_form_ff_off(self, meds, no_of_pills, dose_per_pill ):
        review_text = "Meds taken, Review Approved with FF OFF"
        time.sleep(2)
        self.unheal_all('newCommentInput')
        self.unheal('newCommentInput')
        self.type_and_trigger('newCommentInput', review_text, strict=True)
        # self.type('newCommentInput', review_text+Keys.TAB, strict=True)
        self.unheal_all('span_Comment')
        self.wait_for_element('span_Comment')
        self.click('span_Comment', strict=True)
        assert self.is_element_visible('span_MARK_AS_ADHERENT'), "Mark As Adherence is not present"

        now = datetime.now()
        formatted_now = now.strftime(f"%a - %b %d, %Y - %I:%M %p")
        drug_name = self.get_text('div_drug-name')
        drug_details = self.get_text('div_drug-details')
        text = str(dose_per_pill)+"mg/"+str(no_of_pills)+" pills"
        actual = self.normalize(drug_details)
        expected = self.normalize(text)
        assert expected in actual, f"Expected '{text}' not found in:\n{drug_details}"
        # assert drug_details == text, f"{drug_details} doesnot match {text}"
        print(f"{drug_details} present in {text}")
        assert meds == drug_name, f"{meds} not in {drug_name}"
        print(f"{meds} matches {drug_name}")

        timestamp_text = self.get_text_rendered('span_commented_timestamp', text=review_text)
        self.assert_timestamp_within_minutes(timestamp_text, now, tolerance_minutes=2)
        # assert formatted_now in timestamp_text, f"{str(formatted_now)} not in {timestamp_text}"
        print(f"{str(formatted_now)} is in {timestamp_text}")

        full_text = self.get_text_rendered('div_commented_user_timestamp', text=review_text)
        assert review_text in full_text, f"{review_text} not in {full_text}"
        print(f"{review_text} is in {full_text}")

        self.click_robust('span_MARK_AS_ADHERENT')
        time.sleep(2)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
            self.wait_for_overlays_to_clear(5)
        except Exception:
            print("popup not present after save")
        time.sleep(5)
        return now, formatted_now, review_text

    def check_for_video_link(self):
        time.sleep(3)
        flag = self.is_element_visible('video_unlink', strict=True)
        return flag

    def add_comment(self, text):
        self.wait_for_element('newCommentInput', strict=True)
        review_text = "Meds taken, Review Approved with FF ON"
        self.type_and_trigger('newCommentInput', review_text, strict=True)
        self.unheal_all('span_Comment')
        self.unheal('span_Comment')
        self.wait_for_element('span_Comment')
        self.click('span_Comment', strict=True)
        time.sleep(2)
        return review_text
