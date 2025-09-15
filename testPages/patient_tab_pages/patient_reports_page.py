import random
import time
from datetime import date

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string, fetch_random_digit
from user_inputs.user_data import UserData


class PatientReportsPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def open_patient_reports_page(self):
        self.click('k-tabstrip-tab-Reports')
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Continue")
        except Exception:
            print("popup not present")

    def verify_patient_reports_page(self):
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element('k-opened-tabstrip-tab')
        tabname = self.get_text('k-opened-tabstrip-tab')
        assert tabname == "Reports", "Reports tab is not opened"
        self.wait_for_element('a_Summary_side_effects_and_comments')
        self.wait_for_element('a_Patient_videos')
        print("Opened tab is Reports")

    def verify_comment_and_side_effect(self, comment, side_effect):
        self.click('a_Summary_side_effects_and_comments')
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element('tbody_reports')
        assert self.is_text_in_tbody('tbody_reports', comment), f"{comment} not present in report"
        print( f"{comment} is present in report")
        assert self.is_text_in_tbody('tbody_reports', side_effect), f"{side_effect} not present in report"
        print( f"{side_effect} is present in report")
        self.go_back()

    def verify_video_report(self, upload_date, upload_time):
        self.click('a_Patient_videos')
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element('tbody_reports')
        converted_date = self.convert_date(upload_date)

        assert self.is_text_in_tbody('tbody_reports', str(converted_date)), f"{converted_date} not present in report"
        print( f"{converted_date} is present in report")
        assert self.is_text_in_tbody('tbody_reports', str(upload_time)), f"{upload_time} not present in report"
        print(f"{upload_time} is present in report")
        self.go_back()