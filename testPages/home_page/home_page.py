import time

from common_utilities.base_page import BasePage

class HomePage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def validate_dashboard_page(self):
        self.wait_for_page_to_load()
        self.verify_page_title("SureAdhere", 60)
        self.wait_for_element("p_Dashboard")
        time.sleep(3)

    def click_add_user(self):
        self.click("button_add_user")

    def open_manage_staff_page(self):
        self.click('p_Staff')
        self.wait_for_page_to_load()

    def open_dashboard_page(self):
        self.click('p_Dashboard')
        self.wait_for_page_to_load()

    def click_admin_profile_button(self):
        self.click("button_user_profile")

    def open_manage_patient_page(self):
        self.click('p_Patients')
        self.wait_for_page_to_load()

    def open_admin_page(self):
        self.click('p_Admin')
        time.sleep(5)
        self.wait_for_page_to_load()

