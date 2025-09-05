import time

from common_utilities.base_page import BasePage

class UserProfilePage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def logout_user(self):
        self.click("a_Logout")

