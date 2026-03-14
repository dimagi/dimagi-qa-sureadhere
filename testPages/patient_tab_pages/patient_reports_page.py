import random
import time
from datetime import date, datetime
import re
from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string, fetch_random_digit
from user_inputs.user_data import UserData


class PatientReportsPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def open_patient_reports_page(self):
        self.click('k-tabstrip-tab-Reports', strict=True)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Ok")
        except Exception:
            print("popup not present")

    def verify_patient_reports_page(self):
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
        state = self.get_attribute('k-tabstrip-tab-Reports', 'aria-selected', strict=True)
        self.unheal_all('k-opened-tabstrip-tab')
        time.sleep(3)
        tabname = self.get_text('k-opened-tabstrip-tab')
        print(tabname, state)
        # assert tabname == "Reports", "Reports tab is not opened"
        # assert state == True, "Reports tab is not opened"
        self.wait_for_element('a_Summary_side_effects_and_comments')
        self.wait_for_element('a_Patient_videos')
        assert self.is_element_visible("a_Patient_videos"), "Reports tab is not opened"
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

        date_text = self.get_text("td_video_date")

        assert str(converted_date) == date_text.strip(), f"{converted_date} not present in report"
        print(f"{converted_date} is present in report")

        # assert self.is_text_in_tbody('tbody_reports', str(converted_date)), f"{converted_date} not present in report"
        # print( f"{converted_date} is present in report")

        # assert self.is_text_in_tbody('tbody_reports', str(upload_time)), f"{upload_time} not present in report"
        # print(f"{upload_time} is present in report")

        report_time = self.get_text("td_video_time")

        # Parse both times
        rt = self.round_to_nearest_minute(self.parse_report_time(report_time))
        et = self.round_to_nearest_minute(self.parse_report_time(upload_time))
        delta = abs((rt - et).total_seconds())

        # delta = abs((rt - et).seconds)

        # allow ±2 minutes tolerance
        assert delta < 120, f"{upload_time} not within 2 minutes of report time {report_time}"
        print(f"{upload_time} matched with report time {report_time}")

        self.go_back()

    def validate_report_links(self, reports, flag):
        if flag == False:
            assert self.is_element_visible('td_no_records', strict=True)
        elif flag == True:
            formatted_reports = [self.to_ui_format(x) for x in reports]
            print(formatted_reports)
            for items in formatted_reports:
                assert self.is_element_visible_rendered("a_report_links", text=items)