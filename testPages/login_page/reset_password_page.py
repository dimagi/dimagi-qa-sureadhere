import time

from common_utilities.base_page import BasePage
from testPages.user_profile.user_profile_page import UserProfilePage
from user_inputs.user_data import UserData


class ResetPasswordPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def validate_reset_password_page(self):
        self.wait_for_element('email')
        assert self.is_element_present('Forgot_Password'), "This is not the Reset/Forgot Password Page"
        print("Reset/Forgot Password Page is opened")
        time.sleep(5)

    def enter_email(self, email_address):
        self.wait_for_element("email", 50)
        self.type("email", email_address)
        time.sleep(2)
        self.click("emailVerificationControl_but_send_code")
        time.sleep(3)
        self.wait_for_element('emailVerificationControl_success_message')
        self.wait_for_element('emailVerificationCode')
        text = self.get_text('emailVerificationControl_success_message')
        print(text)
        time.sleep(60)
        print("Waiting for the email to be sent")

    def enter_code(self, code):
        print(code)
        self.wait_for_element("emailVerificationCode", 50)
        self.type("emailVerificationCode", code)
        time.sleep(2)
        self.click("emailVerificationControl_but_verify_code")
        time.sleep(3)
        self.wait_for_element('continue')
        self.wait_for_element('emailVerificationControl_success_message_after')
        text = self.get_text('emailVerificationControl_success_message_after')
        assert text.strip() == UserData.email_verification_success_message_after, "email verification not successful"
        print(text)
        time.sleep(2)
        self.click('continue')
        time.sleep(4)
        self.wait_for_page_to_load(40)


    def enter_new_password(self, password):
        time.sleep(5)
        self.wait_for_element("newPassword", 60)
        self.type('newPassword', password)
        self.type('reenterPassword', password)
        time.sleep(3)
        self.click('continue')
        self.wait_for_page_to_load(40)
        self.wait_for_invisible('continue')
        print("Password reset successfully")

    def click_go_back(self):
        self.wait_for_element('goback')
        self.click('goback')
        time.sleep(2)
        self.wait_for_invisible('goback')
        self.wait_for_page_to_load()