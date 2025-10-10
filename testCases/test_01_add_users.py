import pytest
from seleniumbase import BaseCase

from testPages.home_page.home_page import HomePage
from testPages.login_page.login_page import LoginPage
from testPages.manage_staff_page.manage_staff_page import ManageStaffPage
from testPages.manage_patient_page.manage_patient_page import ManagePatientPage
from testPages.patient_tab_pages.patient_profile_page import PatientProfilePage
from testPages.patient_tab_pages.patient_regimen_page import PatientRegimenPage
from testPages.user_page.user_page import UserPage
from testPages.user_page.user_patient_page import UserPatientPage
from testPages.user_page.user_staff_page import UserStaffPage
from testPages.user_profile.user_profile_page import UserProfilePage
from user_inputs.user_data import UserData


class test_module_01_users(BaseCase):
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

    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_users_1", scope="class")
    def test_case_01_add_staff(self):
        # login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")

        if "banner" in self.settings["url"] or "rogers" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_site_manager = UserData.site_manager[2]
        else:
            default_site_manager = UserData.site_manager[1]

        home.click_add_user()
        user.add_staff()
        fname, lname, email, phn, client, site = user_staff.fill_staff_form(default_site_manager)
        staff.validate_manage_staff_page()
        staff.search_staff(fname, lname, email, phn)
        self.__class__.data.update({"fname": fname, "lname": lname, "email": email, "phn": phn, "isClientAdmint": client, "site": site})
        print(self.data)

    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_users_2", depends=["tc_users_1"], scope="class")
    def test_case_02_edit_staff(self):
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")

        try:
            home.open_dashboard_page()
        except Exception:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()

        home.open_manage_staff_page()
        staff.validate_manage_staff_page()
        d = self.__class__.data  # shared dict

        staff.search_staff(d["fname"], d["lname"], d["email"], d["phn"])
        staff.open_staff(d["fname"], d["lname"])
        new_fname, new_lname, account_active, test_account=user_staff.edit_staff_form(d["fname"], d["lname"], d["email"], d["phn"], client=d["isClientAdmint"])
        home.open_dashboard_page()
        home.open_manage_staff_page()
        staff.validate_manage_staff_page()
        if account_active == False:
            staff.open_inactive_tab()
        elif test_account == True:
            staff.open_test_tab()
        staff.search_staff(new_fname, new_lname, d["email"], d["phn"])
        staff.open_staff(new_fname, new_lname)
        user_staff.wait_for_staff_to_load(new_fname, new_lname)
        user_staff.verify_basic_staff_data(new_fname, new_lname, d["email"], d["phn"], client=d["isClientAdmint"], active=account_active, test=test_account)
        user_staff.make_staff_active(new_fname, new_lname, d["email"], d["phn"])
        self.__class__.data.update(
            {"fname": new_fname, "lname": new_lname, "isActive": account_active, "isTest": test_account}
            )
        print(self.data)

    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_users_3", depends=["tc_users_1", "tc_users_2"], scope="class")
    def test_case_03_add_patient(self):
        rerun_count = getattr(self, "rerun_count", 0)
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        profile = UserProfilePage(self, "user")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        d = self.__class__.data
        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(d["email"], UserData.pwd)
        home.validate_dashboard_page()
        home.click_add_user()
        user.add_patient()
        pfname, plname, mrn, pemail, username, phn, phn_country = user_patient.fill_patient_form(d['site'], rerun_count=rerun_count)
        p_profile.verify_patient_profile_page()
        sa_id = p_profile.verify_patient_profile_details(pfname, plname, mrn, pemail, username, phn, phn_country, d['site'], sa_id=True)
        self.__class__.data.update(
            {"patient_fname": pfname, "patient_lname": plname,
             "patient_email": pemail,
             "patient_phn": phn, "patient_username": username,
             "mrn": mrn, "phone_country":phn_country, "SA_ID": sa_id})

    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_users_4", depends=["tc_users_1", "tc_users_2", "tc_users_3"], scope="class")
    def test_case_04_edit_patient(self):
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        staff = ManageStaffPage(self, "staff")
        patient = ManagePatientPage(self, "patients")
        p_profile = PatientProfilePage(self, 'patient_profile')

        d = self.__class__.data  # shared dict
        try:
            home.open_dashboard_page()
        except Exception:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()

        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()

        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        patient.open_patient(d["patient_fname"], d["patient_lname"])
        new_fname, new_lname, patient_test_account=p_profile.edit_patient_form(d['fname'], d['lname'],
            d["patient_fname"], d["patient_lname"], d['mrn'],
            d["patient_email"], d['patient_username'], d["patient_phn"],
            d['phone_country'], d['site'], d['SA_ID']
            )

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.open_inactive_tab()
        patient.search_patient(new_fname, new_lname, d["mrn"], d["patient_username"], d["SA_ID"])
        patient.open_patient(new_fname, new_lname)
        p_profile.verify_patient_profile_details(new_fname, new_lname, d['mrn'],
            d["patient_email"], d['patient_username'], d["patient_phn"],
            d['phone_country'], d['site'], active_account=patient_test_account)
        # user_staff.verify_basic_staff_data(new_fname, new_lname, d["email"], d["phn"], client=d["isClientAdmin"], active=account_active, test=test_account)
        self.__class__.data.update(
            {"patient_fname": new_fname, "patient_lname": new_lname,
             "is_patient_active": patient_test_account}
            )

    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_users_5", depends=["tc_users_1", "tc_users_2", "tc_users_3", "tc_users_4"], scope="class")
    def test_case_05_set_pin_patient(self):
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        staff = ManageStaffPage(self, "staff")
        patient = ManagePatientPage(self, "patients")
        p_profile = PatientProfilePage(self, 'patient_profile')

        d = self.__class__.data  # shared dict
        try:
            home.open_dashboard_page()
        except Exception:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()

        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.open_inactive_tab()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        patient.open_patient(d["patient_fname"], d["patient_lname"])
        patient_test_account, patient_pin=p_profile.set_patient_pin(d["patient_fname"], d["patient_lname"], d['mrn'],
            d["patient_email"], d['patient_username'], d["patient_phn"],
            d['phone_country'], d['site']
            )
        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        self.__class__.data.update(
            {"is_patient_active": patient_test_account, "patient_pin": patient_pin }
            )

    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_users_6", depends=["tc_users_1", "tc_users_2", "tc_users_3", "tc_users_4", "tc_users_5"], scope="class")
    def test_case_06_new_regimen(self):
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        staff = ManageStaffPage(self, "staff")
        patient = ManagePatientPage(self, "patients")
        p_profile = PatientProfilePage(self, 'patient_profile')
        p_regimen = PatientRegimenPage(self, 'patient_regimens')

        d = self.__class__.data  # shared dict

        try:
            home.open_dashboard_page()
        except Exception:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()

        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        patient.open_patient(d["patient_fname"], d["patient_lname"])
        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()
        start_date, end_date, no_of_pill, med_name, dose_per_pill = p_regimen.create_new_schedule()
        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"], start_date, end_date, no_of_pill)
        self.__class__.data.update(
            {"start_date": start_date, "end_date": end_date,
             "total_pills": no_of_pill, "drug_name":med_name, "dose_per_pill": dose_per_pill}
            )
        print(self.data)


