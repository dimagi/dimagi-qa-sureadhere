import time

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string, fetch_random_digit
from user_inputs.user_data import UserData


class PatientMessagesPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def open_patient_messages_page(self):
        self.click('k-tabstrip-tab-Messages')
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Continue")
        except Exception:
            print("popup not present")


    def verify_patient_messages_page(self):
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element('k-opened-tabstrip-tab')
        tabname = self.get_text('k-opened-tabstrip-tab')
        assert tabname == "Messages", "Messages tab is not opened"
        self.wait_for_element('textarea-message')
        self.wait_for_element('button_send_button')
        print("Opened tab is Messages")

    def read_last_message(self, msg):
        new_text = self.get_last_received_message()
        assert msg in new_text, f"Messages mismatch. {msg} not in {new_text}"
        print(f"{msg} found in {new_text}")

    def send_message(self):
        send_text = "Sending from web " + fetch_random_string()
        self.type('textarea-message', send_text)
        self.click('button_send_button')
        time.sleep(3)
        return send_text


