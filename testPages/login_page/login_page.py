import time

from common_utilities.base_page import BasePage
from testPages.user_profile.user_profile_page import UserProfilePage


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

    def after_logout(self):
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element("next", 60)



