import random
import time

from selenium.webdriver import Keys

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string, fetch_random_digit
from user_inputs.user_data import UserData


class PatientVideoPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)


    def verify_patient_video_page(self):
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element('newCommentInput')
        print("Opened screen is Video Review")

    def fill_up_review_form(self, meds):
        review_text = "Meds taken, Review Approved"
        self.type('newCommentInput', review_text+Keys.TAB)
        # self.click('span_Comment')
        drug_name = self.get_text('div_drug-name')
        assert meds == drug_name, f"{meds} not in {drug_name}"
        print(f"{meds} matches {drug_name}")
        self.click_robust('span_MARK_AS_ADHERENT')
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            assert "Video info saved" in self.kendo_dialog_get_text()
            self.kendo_dialog_click_button("Ok")
            self.wait_for_overlays_to_clear(5)
        except Exception:
            print("popup not present after save")


        # time.sleep(2)
        # self.wait_for_element('kendo-dropdown-saved_status')
        # self.wait_for_element('doseStatus')
        # self.wait_for_element('providerObservation')
        # self.wait_for_element('span_SUBMIT_REVIEW')
        #
        # self.kendo_dd_select_text_old('kendo-dropdown-saved_status', UserData.med_status)
        # saved_status = self.kendo_dd_get_selected_text(logical_name="kendo-dropdown-saved_status")
        # print(f"Selected status is {saved_status}")
        # self.kendo_dd_select_text_old('doseStatus', UserData.med_status)
        # dose_status = self.kendo_dd_get_selected_text(logical_name="doseStatus")
        # print(f"Dose status is {dose_status}")
        # selected_side_effect = random.choice(UserData.side_effect)
        # print(selected_side_effect)
        # self.kendo_dd_select_text_old('providerObservation', UserData.provider_observation)
        # provider_observation = self.kendo_dd_get_selected_text(logical_name="providerObservation")
        # print(f"Provider Observation is {provider_observation}")
        #
        # self.kendo_autocomplete_select("input-side_effects", "selected_side_effect", "selected_side_effect")
        # self.click_robust('span_SUBMIT_REVIEW')
        #
