import pytest
from pytest_dependency import depends
from seleniumbase import BaseCase

from testPages.admin_page.admin_disease_page import AdminDiseasePage
from testPages.admin_page.admin_drug_page import AdminDrugPage
from testPages.admin_page.admin_ff_page import AdminFFPage
from testPages.admin_page.admin_page import AdminPage
from testPages.android.android import Android
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
from testPages.patient_tab_pages.patient_video_page import PatientVideoPage
from testPages.user_page.user_page import UserPage
from testPages.user_page.user_patient_page import UserPatientPage
from testPages.user_profile.user_profile_page import UserProfilePage
from user_inputs.user_data import UserData


class test_module_11_dashboard(BaseCase):
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
    @pytest.mark.dependency(name="tc_dashboard_01", scope="class")
    def test_case_01_verify_dashboard_and_filters(self):
        rerun_count = getattr(self, "rerun_count", 0)
        login = LoginPage(self, "login")
        self._login_once()
        user = UserPage(self, "add_users")
        home = HomePage(self, "dashboard")

        if "banner" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "rogers" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_site_manager = UserData.site_manager[2]
        else:
            default_site_manager = UserData.site_manager[1]

        try:
            home.open_dashboard_page()

        except Exception:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()

        home.validate_dashboard_page()
        home.verify_dashboard_elements()
        home.open_filter()
        home.clear_filter()
        home.open_filter_search_staff("Sites", name=default_site_manager, select=True)
        home.open_filter_search_staff("Treatment Monitor", name=UserData.default_staff_name, select=True)
        home.open_filter_search_staff("Patient Manager", name=UserData.default_staff_name, select=True)
        home.close_filter()
        home.verify_dashboard_table_data(presence=True, patient_manager=UserData.default_staff_name, treatment_monitor=UserData.default_staff_name)

        home.open_filter()
        home.clear_filter()
        home.close_filter()

        home.open_filter()
        home.open_filter_search_staff("Disease", select=True)
        home.verify_dashboard_table_data(presence=True)
        home.clear_filter()
        home.open_filter_search_staff("Observation method", name=UserData.observation_method, select=True)
        home.verify_dashboard_table_data(presence=True, video=True)
        home.clear_filter()
        home.close_filter()


    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_dashboard_02", scope="class")
    def test_case_02_verify_dashboard_quick_actions(self):
        login = LoginPage(self, "login")
        self._login_once()
        user = UserPage(self, "add_users")
        home = HomePage(self, "dashboard")
        p_vdo = PatientVideoPage(self, 'patient_video_form')
        p_message = PatientMessagesPage(self, 'patient_messagess')


        if "banner" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "rogers" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_site_manager = UserData.site_manager[2]
        else:
            default_site_manager = UserData.site_manager[1]

        try:
            home.open_dashboard_page()

        except Exception:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()

        home.validate_dashboard_page()
        home.check_for_quick_actions()
        home.check_for_quick_actions_elements(UserData.quick_actions[0])
        p_vdo.verify_patient_video_page()
        p_vdo.close_form()

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.check_for_quick_actions_elements(UserData.quick_actions[1])
        p_message.verify_patient_messages_page()

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.check_for_quick_actions_elements(UserData.quick_actions[2], select=False)


    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_dashboard_03", scope="class")
    def test_case_03_verify_dashboard_adherence_graph_buttons(self):
        login = LoginPage(self, "login")
        self._login_once()
        user = UserPage(self, "add_users")
        home = HomePage(self, "dashboard")
        p_vdo = PatientVideoPage(self, 'patient_video_form')
        p_message = PatientMessagesPage(self, 'patient_messagess')

        try:
            home.open_dashboard_page()

        except Exception:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()

        home.validate_dashboard_page()
        home.check_for_adherence_section()
        home.change_to_bar_graph(flag=False)
        home.change_to_area_graph(flag=True)
        home.change_to_bar_graph(flag=True)
        home.verify_prev_next_buttons(prev=True)
        home.open_manage_patient_page()
        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.check_for_adherence_section()
        home.verify_prev_next_buttons(next=True)
        home.open_manage_patient_page()





    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_dashboard_04", scope="class")
    def test_case_04_verify_dashboard_adherence_graph_dropdowns(self):
        login = LoginPage(self, "login")
        self._login_once()
        user = UserPage(self, "add_users")
        home = HomePage(self, "dashboard")
        p_vdo = PatientVideoPage(self, 'patient_video_form')
        p_message = PatientMessagesPage(self, 'patient_messagess')

        try:
            home.open_dashboard_page()

        except Exception:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()

        home.validate_dashboard_page()
        home.check_for_adherence_section()
        home.validate_graph_for_selection(UserData.adherence_dropdown[0])
        home.validate_bar_hover_data()
        home.validate_graph_for_selection(UserData.adherence_dropdown[1])
        home.validate_bar_hover_data()


    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_dashboard_05", scope="class")
    def test_case_05_verify_dashboard_adherence_graph_area(self):
        login = LoginPage(self, "login")
        self._login_once()
        user = UserPage(self, "add_users")
        home = HomePage(self, "dashboard")
        p_vdo = PatientVideoPage(self, 'patient_video_form')
        p_message = PatientMessagesPage(self, 'patient_messagess')

        try:
            home.open_dashboard_page()

        except Exception:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()

        home.validate_dashboard_page()
        home.check_for_adherence_section()
        home.change_to_area_graph(flag=True)
        home.adherence_area_graph_hover(UserData.adherence_dropdown[0])
        home.open_manage_patient_page()
        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.check_for_adherence_section()
        home.change_to_area_graph(flag=True)
        home.adherence_area_graph_hover(UserData.adherence_dropdown[1])