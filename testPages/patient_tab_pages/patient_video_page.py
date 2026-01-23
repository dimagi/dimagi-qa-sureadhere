import random
import time
from datetime import datetime

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
        assert drug_details == text, f"{drug_details} doesnot match {text}"
        print(f"{drug_details} matches {text}")
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
            self.click('button_Close')
            self.wait_for_invisible('videoPlayer')
            print("form closed")
        except Exception:
            print("form is not open")

    def verify_video_error(self):
        assert self.is_element_present('video_error'), "Video error not present"
        print("Video error is present")



