import pytest
from seleniumbase import BaseCase

from testPages.email.email_verification import EmailVerification
from testPages.home_page.home_page import HomePage
from testPages.login_page.login_page import LoginPage
from testPages.login_page.reset_password_page import ResetPasswordPage
from testPages.manage_staff_page.manage_staff_page import ManageStaffPage
from testPages.manage_patient_page.manage_patient_page import ManagePatientPage
from testPages.patient_tab_pages.patient_profile_page import PatientProfilePage
from testPages.patient_tab_pages.patient_regimen_page import PatientRegimenPage
from testPages.user_page.user_page import UserPage
from testPages.user_page.user_patient_page import UserPatientPage
from testPages.user_page.user_staff_page import UserStaffPage
from testPages.user_profile.user_profile_page import UserProfilePage
from user_inputs.user_data import UserData


class test_module_04_login_tests(BaseCase):
    data = {}
    _session_ready = False  # guard so we only open/login once

    def _login_once(self):
        """Open browser & login a single time for the whole class."""
        if type(self)._session_ready:
            return
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        login.launch_browser(self.settings["url"])
        login.login(self.settings["login_username"], self.settings["login_password"])
        home.validate_dashboard_page()
        type(self)._session_ready = True


    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_login_10", scope="class")
    def test_case_10_inactivity_10_minutes(self):
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")

        home.validate_dashboard_page()

        home.stay_idle(timeout=10, active=True)
        login.validate_not_login_page()
        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_login_11", scope="class")
    def test_case_11_inactivity_20_minutes(self):
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")

        try:
            login.launch_browser(self.settings["url"])
            login.login(self.settings["login_username"], self.settings["login_password"])
        except Exception:
            home.click_admin_profile_button()
            profile.logout_user()
            login.after_logout()
            login.launch_browser(self.settings["url"])
            login.login(self.settings["login_username"], self.settings["login_password"])


        home.validate_dashboard_page()

        home.stay_idle(timeout=20, active=False)
        login.validate_login_page()

