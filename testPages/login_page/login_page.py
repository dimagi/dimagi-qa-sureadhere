import time

from common_utilities.base_page import BasePage
from testPages.user_profile.user_profile_page import UserProfilePage


class LoginPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def launch_browser(self, url):
        self.launch_url(url)
        self.verify_page_title("Sign in", 60)

    def login(self, username, password):
        self.wait_for_element("next", 50)
        self.type("email", username)
        self.type("password", password)
        self.click("next")

    def after_logout(self):
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element("next", 60)



