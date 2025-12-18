import time

from common_utilities.base_page import BasePage
from testPages.user_profile.user_profile_page import UserProfilePage
from user_inputs.user_data import UserData


class LoginPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def launch_browser(self, url):
        print(f"Launching url {url}")
        self.launch_url(url)
        self.verify_page_title("Sign in", 60)

    def login(self, username, password):
        self.wait_for_element("next", 50)
        self.type("email", username)
        self.type("password", password)
        time.sleep(2)
        self.click("next")
        time.sleep(5)
        self.wait_for_invisible("next")
        self.wait_for_page_to_load(50)
        time.sleep(15)
        print("Logged in successfully with valid Credentials")

    def after_logout(self):
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element("next", 60)
        print("Logged out successfully")

    def invalid_login(self, username, password):
        self.wait_for_element("next", 50)
        self.type("email", username)
        self.type("password", password)
        time.sleep(2)
        self.click("next")
        time.sleep(5)
        self.wait_for_element("invalid_email_password_error")
        text = self.get_text("invalid_email_password_error")
        print(text)
        assert text.strip() in UserData.invalid_credential_error, f"'{text}' did not match any of the errors"
        print("Could not login with invalid credentials")

    def inactive_login(self, username, password):
        self.wait_for_element("next", 50)
        self.type("email", username)
        self.type("password", password)
        time.sleep(2)
        self.click("next")
        time.sleep(5)
        self.wait_for_element("email")
        text = self.get_value("email")
        assert text != username, f"field still contains {username}. Sign in not attempted."
        print("Login attempted with inactive user credentials")

    def validate_login_page(self):
        self.wait_for_page_to_load()
        self.wait_for_element("next", 60)
        assert self.is_element_present("email"), "This is not the Login page"
        print("Login page open successfully!")

    def validate_not_login_page(self):
        self.wait_for_page_to_load(60)
        time.sleep(10)
        assert not self.is_element_visible("next"), "This is the Login page"
        print("This is not Login page!")

    def click_forgot_password(self):
        self.wait_for_element('forgotPassword')
        self.click('forgotPassword')
        time.sleep(3)
        self.wait_for_invisible('forgotPassword', 40)

    def login_with_incorrect_password_with_n_times(self, username, password, n=0):
        self.wait_for_element("next", 50)
        self.type("email", username)
        for i in range(n):
            print(f"Attempting login for {i} time")
            self.type("password", f"{password}_{i}")
            time.sleep(2)
            self.click("next")
            time.sleep(2)
            self.wait_for_element("account_blocked_error")
            text = self.get_text("account_blocked_error")
            print(text)
            if text.strip() == UserData.account_block_error_message:
                print(f"{text} displayed on {i+1}th attempt")
                break
            elif text.strip() in UserData.invalid_credential_error:
                print(f"'{text}' correctly displayed")
            else:
                print(f"invalid message displayed: {text}")

