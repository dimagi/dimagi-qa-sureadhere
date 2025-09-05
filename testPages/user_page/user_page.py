from common_utilities.base_page import BasePage

class UserPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def add_patient(self):
        self.wait_for_element("a_new_patient")
        self.click("a_new_patient")

    def add_staff(self):
        self.wait_for_element("a_new_staff")
        self.click("a_new_staff")
