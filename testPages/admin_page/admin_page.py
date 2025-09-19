import re
import time

from selenium.webdriver import Keys

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string
from user_inputs.user_data import UserData


class AdminPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def validate_admin_page(self):
        self.wait_for_element('kendo-dropdownlist-input-value-Client')
        self.wait_for_element('kendo-expansionpanel_Countries')
        self.wait_for_element('kendo-expansionpanel_Diseases')
        self.wait_for_element('kendo-expansionpanel_Drugs')
        self.wait_for_element('kendo-expansionpanel_Languages')
        text = self.get_text('kendo-dropdownlist-input-value-Client')
        assert text == UserData.site_manager[0], f"Correct Client {UserData.site_manager[0]} is not present"
        print(f"Correct Client {UserData.site_manager[0]} is not present")


    def expand_diseases(self):
        self.wait_for_element("kendo-expansionpanel_Diseases")
        self.kendo_expander_wait("kendo-expansionpanel_Diseases", False)
        self.kendo_expander_set("kendo-expansionpanel_Diseases", True)
        self.kendo_expander_wait("kendo-expansionpanel_Diseases", True)

    def collapse_diseases(self):
        self.wait_for_element("kendo-expansionpanel_Diseases")
        self.kendo_expander_set("kendo-expansionpanel_Diseases", False)
        self.kendo_expander_wait("kendo-expansionpanel_Diseases", False)
        time.sleep(2)

    def expand_drugs(self):
        self.wait_for_element("kendo-expansionpanel_Drugs")
        self.kendo_expander_wait("kendo-expansionpanel_Drugs", False)
        self.kendo_expander_set("kendo-expansionpanel_Drugs", True)
        self.kendo_expander_wait("kendo-expansionpanel_Drugs", True)

    def collapse_drugs(self):
        self.wait_for_element("kendo-expansionpanel_Drugs")
        self.kendo_expander_set("kendo-expansionpanel_Drugs", False)
        self.kendo_expander_wait("kendo-expansionpanel_Drugs", False)
        time.sleep(2)

    def open_announcement(self):
        self.click('k-tabstrip-tab-Announcements')
        self.wait_for_page_to_load()
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Continue")
        except Exception:
            print("popup not present")

    def open_feature_flags(self):
        self.click('k-tabstrip-tab-Feature_Flags')
        self.wait_for_page_to_load()
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            self.kendo_dialog_click_button("Continue")
        except Exception:
            print("popup not present")
