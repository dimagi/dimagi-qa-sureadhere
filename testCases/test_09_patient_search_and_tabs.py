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


class test_module_09_patient_search_and_tabs(BaseCase):
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
    @pytest.mark.dependency(name="tc_pat_search_tabs_1", scope="class")
    def test_case_01_search_patient(self):
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")

        env = self.settings['domain'] if self.settings['domain'] == "rogers" else "others"
        try:
            user_patient.cancel_patient_form()
        except:
            print("Form is already closed")
        try:
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()

        home.open_manage_patient_page()
        patient.search_test_patients("pat_fnmob")
        fname, lname, mrn, username, sa_id = patient.get_details_first_patient()

        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient_with_partial_info(fname=fname, multiple=3)

        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient_with_partial_info(fname=fname, caps=True)

        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.search_patient_with_partial_info(lname=lname, multiple=3)

        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient_with_partial_info(lname=lname, caps=True)

        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient_with_partial_info(fname=fname, lname=lname, multiple=3)

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])

        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient_with_partial_info(fname=fname, lname=lname, caps=True)
        # patient.open_patient(fname, lname)
        # sa_id = patient.get_sa_id()

        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient_with_partial_info(sa_id=sa_id, multiple=3)

        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient_with_partial_info(mrn=mrn, multiple=3)

        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient_with_partial_info(username=username, multiple=3)

        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient_with_partial_info(any="p")

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()


    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_search_tabs_2", scope="class")
    def test_case_02_patient_tab_switch_profile(self):
        rerun_count = getattr(self, "rerun_count", 0)
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")
        p_message = PatientMessagesPage(self, 'patient_messagess')

        env = self.settings['domain'] if self.settings['domain'] == "rogers" else "others"
        if "banner" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "rogers" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_site_manager = UserData.site_manager[2]
        else:
            default_site_manager = UserData.site_manager[1]
        try:
            user_patient.cancel_patient_form()
        except:
            print("Form is already closed")

        try:
            login.launch_browser(self.settings["url"])
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            home.open_dashboard_page()
            home.validate_dashboard_page()

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_test_patients(UserData.client_1_patient_details[env][0])
        fname, lname = patient.open_first_patient()
        p_message.open_patient_messages_page()
        p_message.verify_patient_messages_page()

        home.click_add_user()
        user.add_patient()
        pfname, plname, mrn, pemail, username, phn, phn_country = user_patient.fill_patient_form(default_site_manager, mob="tb", rerun_count=rerun_count)
        p_profile.verify_patient_profile_page()
        sa_id = p_profile.verify_patient_profile_details(pfname, plname, mrn, pemail, username, phn, phn_country, default_site_manager, active_account=True, sa_id=True)
        patient_active_account = p_profile.verify_patient_profile_additional_details()
        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient(pfname, plname, mrn, username, sa_id)
        patient.open_patient(pfname, plname)
        p_profile.select_patient_manager(UserData.default_staff_name)
        p_profile.select_treatment_monitor(UserData.default_staff_name)
        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])

        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient(pfname, plname, mrn, username, sa_id)
        patient.open_patient(pfname, plname)
        p_profile.verify_patient_profile_page()

        self.__class__.data.update(
            {"patient_fname": pfname, "patient_lname": plname,
             "patient_email": pemail,
             "patient_phn": phn, "patient_username": username,
             "mrn": mrn, "phone_country": phn_country, "SA_ID": sa_id,
             "site": default_site_manager, "is_patient_active": patient_active_account,
             "env": env
             }
            )

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_search_tabs_3", depends=['tc_pat_search_tabs_2'], scope="class")
    def test_case_03_patient_tab_switch_overview(self):
        rerun_count = getattr(self, "rerun_count", 0)
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")
        p_message = PatientMessagesPage(self, 'patient_messagess')
        p_overview = PatientOverviewPage(self, 'patient_overview')

        d = self.__class__.data
        try:
            user_patient.cancel_patient_form()
        except:
            print("Form is already closed")
        try:
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            login.launch_browser(self.settings["url"])
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient(d['patient_fname'], d['patient_lname'], d['mrn'], d['patient_username'], d['SA_ID'])
        patient.open_patient(d['patient_fname'], d['patient_lname'])
        p_overview.open_patient_overview_page()
        p_overview.verify_patient_overview_page()

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])

        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_test_patients(UserData.client_1_patient_details[d["env"]][0])
        fname, lname = patient.open_first_patient()
        p_overview.verify_patient_overview_page()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_search_tabs_4", depends=['tc_pat_search_tabs_2'], scope="class")
    def test_case_04_patient_tab_switch_adherence(self):
        rerun_count = getattr(self, "rerun_count", 0)
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")
        p_adhere = PatientAdherencePage(self, 'patient_adherence')

        d = self.__class__.data

        try:
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            login.launch_browser(self.settings["url"])
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient(d['patient_fname'], d['patient_lname'], d['mrn'], d['patient_username'], d['SA_ID'])
        patient.open_patient(d['patient_fname'], d['patient_lname'])
        p_adhere.open_patient_adherence_page()
        p_adhere.verify_patient_adherence_page()

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])

        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_test_patients(UserData.client_1_patient_details[d["env"]][0])
        fname, lname = patient.open_first_patient()
        p_adhere.verify_patient_adherence_page()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_search_tabs_5", depends=['tc_pat_search_tabs_2'], scope="class")
    def test_case_05_patient_tab_switch_regimen(self):
        rerun_count = getattr(self, "rerun_count", 0)
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")
        p_regimen = PatientRegimenPage(self, 'patient_regimens')

        d = self.__class__.data

        try:
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            login.launch_browser(self.settings["url"])
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient(d['patient_fname'], d['patient_lname'], d['mrn'], d['patient_username'], d['SA_ID'])
        patient.open_patient(d['patient_fname'], d['patient_lname'])
        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])

        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_test_patients(UserData.client_1_patient_details[d["env"]][0])
        fname, lname = patient.open_first_patient()
        p_regimen.verify_patient_regimen_page()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_search_tabs_6", depends=['tc_pat_search_tabs_2'], scope="class")
    def test_case_06_patient_tab_switch_message(self):
        rerun_count = getattr(self, "rerun_count", 0)
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")
        p_message = PatientMessagesPage(self, 'patient_messagess')

        d = self.__class__.data

        try:
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            login.launch_browser(self.settings["url"])
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient(d['patient_fname'], d['patient_lname'], d['mrn'], d['patient_username'], d['SA_ID'])
        patient.open_patient(d['patient_fname'], d['patient_lname'])
        p_message.open_patient_messages_page()
        p_message.verify_patient_messages_page()

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])

        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_test_patients(UserData.client_1_patient_details[d["env"]][0])
        fname, lname = patient.open_first_patient()
        p_message.verify_patient_messages_page()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_search_tabs_7a", scope="class")
    def test_case_07a_pill_count_ff_setup_on(self):
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        admin = AdminPage(self, 'admin')
        a_ff = AdminFFPage(self, 'feature_flags')


        if "banner" in self.settings["url"]:
            default_client = UserData.client[0]
            flag = True
        elif "rogers" in self.settings["url"]:
            default_client = UserData.client[1]
            flag = False
        elif "securevoteu" in self.settings["url"]:
            default_client = UserData.client[3]
            flag = False
        else:
            default_client = UserData.client[2]
            flag = True
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
        a_ff.set_ffs(UserData.pill_count_ff_on, flag)
        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.double_check_ff(UserData.pill_count_ff_on, flag)

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_search_tabs_7", depends=['tc_pat_search_tabs_2', 'tc_pat_search_tabs_7a'], scope="class")
    def test_case_07b_patient_tab_switch_pill_count(self):
        rerun_count = getattr(self, "rerun_count", 0)
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")
        p_pill = PatientPillCountPage(self, 'patient_pill_count')

        d = self.__class__.data

        try:
            login.login(self.settings["login_username"], self.settings["login_password"])
        except Exception:
            print("Not in the login page")
            home.click_admin_profile_button()
            profile.logout_user()
            login.after_logout()
            login.login(self.settings["login_username"], self.settings["login_password"])

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient(d['patient_fname'], d['patient_lname'], d['mrn'], d['patient_username'], d['SA_ID'])
        patient.open_patient(d['patient_fname'], d['patient_lname'])
        p_pill.open_patient_pill_count_page()
        p_pill.verify_patient_pill_count_page()

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])

        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_test_patients(UserData.client_1_patient_details[d["env"]][0])
        fname, lname = patient.open_first_patient()
        p_pill.verify_patient_pill_count_page()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_search_tabs_7c", depends=['tc_pat_search_tabs_7', 'tc_pat_search_tabs_7a'], scope="class")
    def test_case_07c_pill_count_ff_setup_off(self):
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        admin = AdminPage(self, 'admin')
        a_ff = AdminFFPage(self, 'feature_flags')

        if "banner" in self.settings["url"]:
            default_client = UserData.client[0]
            flag = True
        elif "rogers" in self.settings["url"]:
            default_client = UserData.client[1]
            flag = False
        elif "securevoteu" in self.settings["url"]:
            default_client = UserData.client[3]
            flag = False
        else:
            default_client = UserData.client[2]
            flag = True

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
        a_ff.set_ffs(UserData.pill_count_ff_off, flag)
        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.double_check_ff(UserData.pill_count_ff_off, flag)



    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_search_tabs_8", depends=['tc_pat_search_tabs_2'], scope="class")
    def test_case_08_patient_tab_switch_report(self):
        rerun_count = getattr(self, "rerun_count", 0)
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")
        p_report = PatientReportsPage(self, 'patient_reports')

        d = self.__class__.data

        try:
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            login.launch_browser(self.settings["url"])
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_patient(d['patient_fname'], d['patient_lname'], d['mrn'], d['patient_username'], d['SA_ID'])
        patient.open_patient(d['patient_fname'], d['patient_lname'])
        p_report.open_patient_reports_page()
        p_report.verify_patient_reports_page()

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])

        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_test_patients(UserData.client_1_patient_details[d["env"]][0])
        fname, lname = patient.open_first_patient()
        p_report.verify_patient_reports_page()
