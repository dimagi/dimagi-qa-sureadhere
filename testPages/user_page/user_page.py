import time

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
        time.sleep(4)

    def validate_staff_presence(self, presence=True):
        if presence:
            assert self.is_element_visible("a_new_staff"), "Create Staff option not present"
            print("Create Staff option is present")
        else:
            assert not self.is_element_visible("a_new_staff"), "Create Staff option is present"
            print("Create Staff option not present")
        time.sleep(4)

    def validate_patient_presence(self, presence=True):
        if presence:
            assert self.is_element_visible("a_new_patient"), "Create Patient option not present"
            print("Create Patient option is present")
        else:
            assert not self.is_element_visible("a_new_patient"), "Create Patient option is present"
            print("Create Patient option not present")
        time.sleep(4)
