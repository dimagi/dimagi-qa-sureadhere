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
    @pytest.mark.dependency(name="tc_login_0", scope="class")
    def test_case_00_presetup_add_staff(self):
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")
        profile = UserProfilePage(self, "user")
        login = LoginPage(self, "login")

        if "banner" in self.settings["url"] or "rogers" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_site_manager = UserData.site_manager[2]
        else:
            default_site_manager = UserData.site_manager[1]

        home.click_add_user()
        user.add_staff()
        fname, lname, email, phn, client, site = user_staff.fill_staff_form(default_site_manager, login="log")
        staff.validate_manage_staff_page()
        staff.search_staff(fname, lname, email, phn)
        self.__class__.data.update({"fname": fname, "lname": lname, "email": email, "phn": phn, "isClientAdmint": client, "site": site})
        print(self.data)

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_login_1", scope="class")
    def test_case_01_sign_in_and_out_valid_credentials(self):
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")

        login.login(self.settings["login_username"], self.settings["login_password"])
        home.validate_dashboard_page()

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_login_2", scope="class")
    def test_case_02_sign_in_incorrect_password(self):
        self._login_once()
        login = LoginPage(self, "login")

        login.invalid_login(self.settings["login_username"], UserData.invalid_password)

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_login_3", scope="class")
    def test_case_03_sign_in_incorrect_email(self):
        self._login_once()
        login = LoginPage(self, "login")

        login.invalid_login(UserData.invalid_email, self.settings["login_password"])

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_login_4", scope="class")
    def test_case_04_sign_in_inactive_user(self):
        self._login_once()
        login = LoginPage(self, "login")

        email_address = UserData.inactive_user_email_rogers if "rogers" in self.settings[
            'domain'] else UserData.inactive_user_email
        print(self.settings["domain"])

        login.inactive_login(email_address, UserData.pwd)


    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_login_5", scope="class")
    def test_case_05_reset_password(self):
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        email = EmailVerification(self.settings)
        profile = UserProfilePage(self, "user")
        reset = ResetPasswordPage(self, "reset_password")

        target_email = UserData.reset_email_address_rogers if "rogers" in self.settings[
            'domain'] else UserData.reset_email_address
        print(self.settings["domain"])

        login.login(target_email, UserData.pwd)

        home.validate_dashboard_page()
        home.click_admin_profile_button()
        profile.reset_password()

        reset.validate_reset_password_page()
        reset.enter_email(target_email)

        code = email.get_verification_code_from_email(UserData.reset_password_email_subject[self.settings["domain"]], target_email)

        reset.enter_code(code)
        reset.enter_new_password(UserData.pwd)

        home.validate_dashboard_page()
        home.click_admin_profile_button()
        profile.validate_logged_in_user(target_email)
        profile.logout_user()
        login.after_logout()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_login_6", scope="class")
    def test_case_06_forgot_password(self):
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        email = EmailVerification(self.settings)
        profile = UserProfilePage(self, "user")
        reset = ResetPasswordPage(self, "reset_password")

        target_email = UserData.reset_email_address_rogers if "rogers" in self.settings['domain'] else UserData.reset_email_address

        try:
            login.launch_browser(self.settings["url"])
        except Exception:
            home.click_admin_profile_button()
            profile.logout_user()
            login.after_logout()
            login.launch_browser(self.settings["url"])
        login.click_forgot_password()

        reset.validate_reset_password_page()
        reset.enter_email(target_email)

        code = email.get_verification_code_from_email(UserData.reset_password_email_subject[self.settings["domain"]], target_email)

        reset.enter_code(code)
        reset.enter_new_password(UserData.pwd)

        home.validate_dashboard_page()
        home.click_admin_profile_button()
        profile.validate_logged_in_user(target_email)
        profile.logout_user()
        login.after_logout()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_login_7", scope="class")
    def test_case_07_reset_password_of_other_user(self):
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        email = EmailVerification(self.settings)
        profile = UserProfilePage(self, "user")
        reset = ResetPasswordPage(self, "reset_password")

        target_email = UserData.reset_email_address_rogers if "rogers" in self.settings[
            'domain'] else UserData.reset_email_address
        print(self.settings["domain"])
        try:
            login.launch_browser(self.settings["url"])
        except Exception:
            home.click_admin_profile_button()
            profile.logout_user()
            login.after_logout()
            login.launch_browser(self.settings["url"])

        login.login(self.settings["login_username"], self.settings["login_password"])

        home.validate_dashboard_page()
        home.click_admin_profile_button()
        profile.reset_password()

        reset.validate_reset_password_page()
        reset.enter_email(target_email)

        code = email.get_verification_code_from_email(UserData.reset_password_email_subject[self.settings["domain"]], target_email)

        reset.enter_code(code)
        reset.enter_new_password(UserData.pwd)

        home.validate_dashboard_page()
        home.click_admin_profile_button()
        try:
            profile.validate_user_profile_open()
        except Exception:
            home.click_admin_profile_button()
            profile.validate_user_profile_open()

        profile.validate_logged_in_user(target_email)
        profile.logout_user()
        login.after_logout()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_login_8", scope="class")
    def test_case_08_reset_password_go_back(self):
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        reset = ResetPasswordPage(self, "reset_password")

        target_email = UserData.reset_email_address_rogers if "rogers" in self.settings[
            'domain'] else UserData.reset_email_address
        print(self.settings["domain"])

        try:
            login.login(target_email, UserData.pwd)
        except Exception:
            home.click_admin_profile_button()
            profile.logout_user()
            login.after_logout()
            login.login(target_email, UserData.pwd)

        home.validate_dashboard_page()
        home.click_admin_profile_button()
        profile.reset_password()

        reset.validate_reset_password_page()
        reset.click_go_back()
        home.validate_dashboard_page()
        try:
            profile.validate_user_profile_open()
            profile.validate_logged_in_user(target_email)
        except Exception:
            home.click_admin_profile_button()
            home.click_admin_profile_button()
            profile.validate_user_profile_open()
            profile.validate_logged_in_user(target_email)
        profile.logout_user()
        login.after_logout()


    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_login_9", scope="class")
    def test_case_09_forgot_password_go_back(self):
        self._login_once()
        login = LoginPage(self, "login")
        reset = ResetPasswordPage(self, "reset_password")
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")

        print(self.settings["domain"])


        try:
            login.validate_login_page()
        except Exception:
            home.click_admin_profile_button()
            profile.logout_user()
            login.after_logout()
            login.validate_login_page()

        login.click_forgot_password()

        reset.validate_reset_password_page()
        reset.click_go_back()
        login.validate_login_page()


    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_login_12", scope="class")
    def test_case_12_client_based_patient_access(self):
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        patient = ManagePatientPage(self, "patients")

        try:
            login.validate_login_page()
        except Exception:
            home.click_admin_profile_button()
            profile.logout_user()
            login.after_logout()
            login.validate_login_page()

        env = self.settings['domain'] if self.settings['domain'] == "rogers" else "others"
        print(self.settings['domain'], env)

        # client 1 patient access
        login.login(UserData.client_1_staff_details[env][1], UserData.pwd)
        home.open_manage_patient_page()
        patient.search_test_patients(UserData.client_1_patient_details[env][0])
        patient.search_test_patients_not_present(UserData.client_2_patient_details[env][0])

        home.validate_dashboard_page()
        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        # client 2 patient access
        login.login(UserData.client_2_staff_details[env][1], UserData.pwd)
        home.open_manage_patient_page()
        patient.search_test_patients(UserData.client_2_patient_details[env][0])
        patient.search_test_patients_not_present(UserData.client_1_patient_details[env][0])

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_login_14", scope="class")
    def test_case_14_incorrect_password_to_block_account(self):
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        d = self.__class__.data

        try:
            login.validate_login_page()
        except Exception:
            home.click_admin_profile_button()
            profile.logout_user()
            login.after_logout()
            login.validate_login_page()
        login.login_with_incorrect_password_with_n_times(d['email'], UserData.invalid_password, 10)
