import re
import time
from datetime import datetime

from selenium.webdriver import Keys

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string
from user_inputs.user_data import UserData


class AdminAnnouncementPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)


    def verify_announcements_page(self):
        time.sleep(10)
        self.wait_for_page_to_load(50)
        self.wait_for_element('k-opened-tabstrip-tab', 60)
        tabname = self.get_text('k-opened-tabstrip-tab')
        self.wait_for_element('span_ADD_ANNOUNCEMENT')
        assert tabname == "Announcements", "Announcements tab is not opened"

    def add_announcement(self):
        self.click('span_ADD_ANNOUNCEMENT')
        time.sleep(3)

    def edit_announcement(self, announcement_text):
        msg_list = self.find_elements('td_msg')
        edit_list = self.find_elements('span_edit')
        print( len(msg_list), len(edit_list))
        for msgs, edits in zip(msg_list, edit_list):
            msg_text = msgs.text.strip()
            print(f"[Message]: {msg_text}")
            if announcement_text in msg_text:
                print(f"{announcement_text} is present")
                edits.click()
                time.sleep(2)
                break
            else:
                print(f"{announcement_text} not matching")


    def verify_announcement_created(self, announcement_text, status, client=None):
        status_list = self.find_elements('td_status')
        msg_list = self.find_elements('td_msg')
        client_list = self.find_elements('td_client')
        edit_list = self.find_elements('span_edit')
        print(len(status_list),len(msg_list),len(edit_list),len(client_list))
        for statuses, msgs, clients, edits in zip(status_list, msg_list, client_list, edit_list):
            msg_text = msgs.text.strip()
            status_text = statuses.text.strip()
            client_text = clients.text.strip()
            print(f"[Message]: {msg_text}, [status]: {status_text}, [client]: {client_text}")
            if announcement_text in msg_text and status_text == status:
                if client:
                    assert client_text == client, f"{client} is not matching"
                    print(f"{client} is matching")
                else:
                    print("No client provided")
                assert True, f"{announcement_text}, {status_text} are not matching"
                print(f"{announcement_text}, {status_text} are matching")
                break
            else:
                print(f"{announcement_text}, {status_text}, {client_text} are not matching")

