import time

from common_utilities.base_page import BasePage

class UserProfilePage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def validate_user_profile_open(self):
        self.wait_for_element('current-user-name')
        assert self.is_element_present('a_Reset_password'), "Reset password not present"
        assert self.is_element_present('a_Logout'), "Logout not present"
        print("User Profile is displayed")

    def logout_user(self):
        self.wait_for_element('a_Logout')
        self.click("a_Logout")

    def reset_password(self):
        self.wait_for_element('a_Reset_password')
        self.click('a_Reset_password')
        self.wait_for_page_to_load()

    def validate_logged_in_user(self, user_email):
        self.wait_for_element('current-user-name')
        text = self.get_text('current-user-name')
        print(text)
        assert text.strip() == user_email, f"Not logged in as {user_email}"
        print(f"Currently logged in as {user_email}")

