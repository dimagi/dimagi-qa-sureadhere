import pytest
from pytest_dependency import depends
from seleniumbase import BaseCase

from testPages.admin_page.admin_ff_page import AdminFFPage
from testPages.admin_page.admin_page import AdminPage
from testPages.home_page.home_page import HomePage
from testPages.login_page.login_page import LoginPage
from testPages.manage_patient_page.manage_patient_page import ManagePatientPage
from testPages.patient_tab_pages.patient_adherence_page import PatientAdherencePage
from testPages.patient_tab_pages.patient_messages_page import PatientMessagesPage
from testPages.patient_tab_pages.patient_overview_page import PatientOverviewPage
from testPages.patient_tab_pages.patient_pill_count_page import PatientPillCountPage
from testPages.patient_tab_pages.patient_profile_page import PatientProfilePage
from testPages.patient_tab_pages.patient_regimen_page import PatientRegimenPage
from testPages.patient_tab_pages.patient_reports_page import PatientReportsPage
from testPages.user_page.user_page import UserPage
from testPages.user_page.user_patient_page import UserPatientPage
from testPages.user_profile.user_profile_page import UserProfilePage
from user_inputs.user_data import UserData


class test_module_10_patient_search_and_tabs(BaseCase):
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
    @pytest.mark.dependency(name="tc_pat_pill_count_00", scope="class")
    def test_case_00_pill_count_ff_check(self):
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        admin = AdminPage(self, 'admin')
        a_ff = AdminFFPage(self, 'feature_flags')
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")
        p_pill = PatientPillCountPage(self, 'patient_pill_count')

        if "banner" in self.settings["url"]:
            default_client = UserData.client[0]
        elif "rogers" in self.settings["url"]:
            default_client = UserData.client[1]
        elif "securevoteu" in self.settings["url"]:
            default_client = UserData.client[3]
        else:
            default_client = UserData.client[2]

        try:
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            login.launch_browser(self.settings["url"])
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()

        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.set_ffs(UserData.pill_count_ff_off)
        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.double_check_ff(UserData.pill_count_ff_off)

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_test_patients()
        patient.open_first_patient()
        p_pill.verify_patient_pill_count_page_presence(False)

        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.set_ffs(UserData.pill_count_ff_on)
        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.double_check_ff(UserData.pill_count_ff_on)

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_test_patients()
        patient.open_first_patient()
        p_pill.verify_patient_pill_count_page_presence(True)

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()


    # @pytest.mark.extendedtests
    # @pytest.mark.dependency(name="tc_pat_pill_count_01", scope="class")
    # def test_case_01_regimen_approval_ff_on(self):
    #     login = LoginPage(self, "login")
    #     self._login_once()
    #     home = HomePage(self, "dashboard")
    #     admin = AdminPage(self, 'admin')
    #     a_ff = AdminFFPage(self, 'feature_flags')
    #     patient = ManagePatientPage(self, "patients")
    #     profile = UserProfilePage(self, "user")
    #     p_pill = PatientPillCountPage(self, 'patient_pill_count')
    #     p_regimen = PatientRegimenPage(self, 'patient_regimens')
    #
    #     env = self.settings['domain'] if self.settings['domain'] == "rogers" else "others"
    #
    #     if "banner" in self.settings["url"]:
    #         default_client = UserData.client[0]
    #     elif "rogers" in self.settings["url"]:
    #         default_client = UserData.client[1]
    #     elif "securevoteu" in self.settings["url"]:
    #         default_client = UserData.client[3]
    #     else:
    #         default_client = UserData.client[2]
    #
    #     try:
    #         login.login(self.settings["login_username"], self.settings["login_password"])
    #         home.open_dashboard_page()
    #         home.validate_dashboard_page()
    #     except Exception:
    #         home.open_dashboard_page()
    #         home.validate_dashboard_page()
    #
    #     # home.open_admin_page()
    #     # admin.open_feature_flags()
    #     # a_ff.validate_admin_ff_page(default_client)
    #     # a_ff.set_ffs(UserData.regimen_approval_ff_on)
    #     # home.open_dashboard_page()
    #     # home.validate_dashboard_page()
    #     # home.open_admin_page()
    #     # admin.open_feature_flags()
    #     # a_ff.validate_admin_ff_page(default_client)
    #     # a_ff.double_check_ff(UserData.regimen_approval_ff_on)
    #
    #     home.open_dashboard_page()
    #     home.open_manage_patient_page()
    #     patient.validate_manage_patient_page()
    #     patient.search_test_patients(UserData.client_1_patient_details[env][0])
    #     patient.open_first_patient()
    #     p_regimen.open_patient_regimen_page()
    #     p_regimen.verify_patient_regimen_page()
    #     list_names =  p_regimen.get_pill_names()
    #     print(list_names)
        p_regimen.delete_schedule()


