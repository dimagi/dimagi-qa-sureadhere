import pytest
from pytest_dependency import depends
from seleniumbase import BaseCase

from testPages.admin_page.admin_disease_page import AdminDiseasePage
from testPages.admin_page.admin_drug_page import AdminDrugPage
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


class test_module_10_patient_pill_count(BaseCase):
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

        try:
            home.click_admin_profile_button()
            profile.logout_user()
            login.after_logout()
            login.login(self.settings["login_username"], self.settings["login_password"])
        except:
            login.login(self.settings["login_username"], self.settings["login_password"])

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


    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_pill_count_01", scope="class")
    def test_case_01_regimen_approval_ff_on(self):
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        admin = AdminPage(self, 'admin')
        a_ff = AdminFFPage(self, 'feature_flags')
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")
        p_pill = PatientPillCountPage(self, 'patient_pill_count')
        p_regimen = PatientRegimenPage(self, 'patient_regimens')

        env = self.settings['domain'] if self.settings['domain'] == "rogers" else "others"

        if "banner" in self.settings["url"]:
            default_client = UserData.client[0]
        elif "rogers" in self.settings["url"]:
            default_client = UserData.client[1]
        elif "securevoteu" in self.settings["url"]:
            default_client = UserData.client[3]
        else:
            default_client = UserData.client[2]

        try:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            home.open_dashboard_page()
            home.validate_dashboard_page()

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_test_patients(UserData.client_1_patient_details[env][0])
        patient.open_first_patient()
        p_regimen.open_patient_regimen_page()
        p_regimen.delete_schedule()

        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.set_ffs(UserData.regimen_approval_ff_on)
        a_ff.set_ffs(UserData.pill_count_ff_on)

        home.validate_dashboard_page()
        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.double_check_ff(UserData.regimen_approval_ff_on)
        a_ff.double_check_ff(UserData.pill_count_ff_on)

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.login(self.settings["login_username"], self.settings["login_password"])

        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_test_patients(UserData.client_1_patient_details[env][0])
        patient.open_first_patient()
        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()
        p_regimen.create_new_schedule(disease_flag=False)
        p_regimen.verify_regimen_approval_error()

        p_pill.open_patient_pill_count_page()
        p_pill.verify_pill_count_error()

        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()
        p_regimen.delete_schedule()

        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.set_ffs(UserData.regimen_approval_ff_off)
        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.double_check_ff(UserData.regimen_approval_ff_off)

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_pill_count_02", scope="class")
    def test_case_02_ff_drug_setup(self):
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        admin = AdminPage(self, 'admin')
        a_ff = AdminFFPage(self, 'feature_flags')
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")
        p_pill = PatientPillCountPage(self, 'patient_pill_count')
        p_regimen = PatientRegimenPage(self, 'patient_regimens')
        a_drug = AdminDrugPage(self, 'admin_drugs')

        env = self.settings['domain'] if self.settings['domain'] == "rogers" else "others"

        if "banner" in self.settings["url"]:
            default_client = UserData.client[0]
        elif "rogers" in self.settings["url"]:
            default_client = UserData.client[1]
        elif "securevoteu" in self.settings["url"]:
            default_client = UserData.client[3]
        else:
            default_client = UserData.client[2]

        try:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            home.open_dashboard_page()
            home.validate_dashboard_page()

        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.set_ffs(UserData.regimen_approval_ff_off)
        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.double_check_ff(UserData.regimen_approval_ff_off)
        home.open_dashboard_page()

        try:
            home.click_admin_profile_button()
            profile.logout_user()
            login.after_logout()
            login.login(self.settings["login_username"], self.settings["login_password"])
        except:
            login.login(self.settings["login_username"], self.settings["login_password"])


        home.open_admin_page()
        admin.open_config_lookup()
        admin.validate_admin_page(default_client)
        admin.expand_drugs()
        drug_switch, drug_name = a_drug.toggle_for_drugs(UserData.pill_count_drug, "ON")

        home.open_dashboard_page()
        home.open_admin_page()
        admin.validate_admin_page(default_client)
        admin.expand_drugs()
        a_drug.double_check_on_toggle(drug_name, drug_switch)


    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_pill_count_03", scope="class")
    def test_case_03_add_pill_count(self):
        rerun_count = getattr(self, "rerun_count", 0)
        login = LoginPage(self, "login")
        self._login_once()
        user = UserPage(self, "add_users")
        home = HomePage(self, "dashboard")
        admin = AdminPage(self, 'admin')
        a_ff = AdminFFPage(self, 'feature_flags')
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")
        p_pill = PatientPillCountPage(self, 'patient_pill_count')
        p_regimen = PatientRegimenPage(self, 'patient_regimens')
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')

        # env = self.settings['domain'] if self.settings['domain'] == "rogers" else "others"

        if "banner" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "rogers" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_site_manager = UserData.site_manager[2]
        else:
            default_site_manager = UserData.site_manager[1]

        try:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            home.open_dashboard_page()
            home.validate_dashboard_page()
        # fname = "pat_fn_04b85u_new"
        # lname = "pat_ln_04b85u_new"
        # home.open_dashboard_page()
        # home.validate_dashboard_page()
        home.click_add_user()
        user.add_patient()
        fname, lname, mrn, pemail, username, phn, phn_country = user_patient.fill_patient_form(default_site_manager,
                                                                                                 mob='pl',
                                                                                                 rerun_count=rerun_count
                                                                                                 )
        p_profile.verify_patient_profile_page()
        sa_id = p_profile.verify_patient_profile_details(fname, lname, mrn, pemail, username, phn, phn_country,
                                                         default_site_manager, sa_id=True
                                                         )

        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()
        p_regimen.create_new_schedule(disease_flag=False, drug_name=UserData.pill_count_drug)
        p_regimen.create_new_schedule(disease_flag=False)
        name_list = p_regimen.get_pill_names()
        p_pill.open_patient_pill_count_page()
        date_list, visit_date, return_date = p_pill.add_pill_count(drug_name=name_list)
        print(date_list)

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        self.__class__.data.update(
            {"patient_fname": fname, "patient_lname": lname,
             "patient_email": pemail,
             "patient_phn": phn, "patient_username": username,
             "mrn": mrn, "phone_country": phn_country, "SA_ID": sa_id,
             "site": default_site_manager, "drug_name_list": name_list,
             "date_list": date_list, "visit_date": visit_date, "return_date": return_date,
             }
            )

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_pill_count_04", depends=['tc_pat_pill_count_03'], scope="class")
    def test_case_04_edit_pill_count(self):
        d = self.__class__.data
        login = LoginPage(self, "login")
        self._login_once()
        user = UserPage(self, "add_users")
        home = HomePage(self, "dashboard")
        admin = AdminPage(self, 'admin')
        a_ff = AdminFFPage(self, 'feature_flags')
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")
        p_pill = PatientPillCountPage(self, 'patient_pill_count')
        p_regimen = PatientRegimenPage(self, 'patient_regimens')
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')

        if "banner" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "rogers" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_site_manager = UserData.site_manager[2]
        else:
            default_site_manager = UserData.site_manager[1]

        try:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            home.open_dashboard_page()
            home.validate_dashboard_page()

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_test_patients(d['patient_fname']+" "+d['patient_lname'])

        fname, lname = patient.open_first_patient()
        print(fname, lname)
        p_regimen.open_patient_regimen_page()
        p_pill.open_patient_pill_count_page()
        date_list_new = p_pill.edit_pill_count(date_list=d['date_list'], drug_name=d['drug_name_list'], visit_date=d['visit_date'], return_date=d['return_date'])
        print(date_list_new)

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        self.__class__.data.update(
            {
             "date_list": date_list_new
             }
            )

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_pill_count_05", depends=['tc_pat_pill_count_03', 'tc_pat_pill_count_04'], scope="class")
    def test_case_05_delete_pill_count(self):
        d = self.__class__.data
        login = LoginPage(self, "login")
        self._login_once()
        user = UserPage(self, "add_users")
        home = HomePage(self, "dashboard")
        admin = AdminPage(self, 'admin')
        a_ff = AdminFFPage(self, 'feature_flags')
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")
        p_pill = PatientPillCountPage(self, 'patient_pill_count')
        p_regimen = PatientRegimenPage(self, 'patient_regimens')
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')

        if "banner" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "rogers" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_site_manager = UserData.site_manager[2]
        else:
            default_site_manager = UserData.site_manager[1]

        try:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            home.open_dashboard_page()
            home.validate_dashboard_page()

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_test_patients(d['patient_fname'] + " " + d['patient_lname'])

        fname, lname = patient.open_first_patient()
        print(fname, lname)
        p_regimen.open_patient_regimen_page()
        p_pill.open_patient_pill_count_page()
        p_pill.delete_pill_count(date_list=d['date_list'], drug_name=d['drug_name_list'])

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()