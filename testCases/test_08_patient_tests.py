import pytest
from pytest_dependency import depends
from seleniumbase import BaseCase

from testPages.home_page.home_page import HomePage
from testPages.login_page.login_page import LoginPage
from testPages.manage_patient_page.manage_patient_page import ManagePatientPage
from testPages.patient_tab_pages.patient_profile_page import PatientProfilePage
from testPages.patient_tab_pages.patient_regimen_page import PatientRegimenPage
from testPages.user_page.user_page import UserPage
from testPages.user_page.user_patient_page import UserPatientPage
from testPages.user_profile.user_profile_page import UserProfilePage
from user_inputs.user_data import UserData


class test_module_08_patient_tests(BaseCase):
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
    @pytest.mark.dependency(name="tc_patient_1", scope="class")
    def test_case_01_leave_patient_mandatory_details(self):
        self._login_once()
        rerun_count = getattr(self, "rerun_count", 0)
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        user_patient = UserPatientPage(self, "add_patient")
        login = LoginPage(self, "login")
        profile = UserProfilePage(self, "user")

        if "banner" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "rogers" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_site_manager = UserData.site_manager[2]
        else:
            default_site_manager = UserData.site_manager[1]

        try:
            user_patient.cancel_form()
        except:
            print("No dialog present")
        try:
            if rerun_count != 0:
                home.click_admin_profile_button()
                profile.logout_user()
                login.after_logout()
                login.validate_login_page()
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.validate_dashboard_page()
        except:
            print("Already logged in")
            home.open_dashboard_page()

        home.click_add_user()
        user.add_patient()
        user_patient.leave_mandatory_fields_patient_form(default_site_manager,mob='man',rerun_count=rerun_count)

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_patient_2", scope="class")
    def test_case_02_add_patient_with_all_details(self):
        rerun_count = getattr(self, "rerun_count", 0)
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        profile = UserProfilePage(self, "user")
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
            user_patient.cancel_patient_form()
        except:
            print("Form is already closed")
        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.click_add_user()
        user.add_patient()
        pfname, plname, mrn, pemail, username, phn, phn_country = user_patient.fill_patient_form(default_site_manager, mob="ex", rerun_count=rerun_count)
        p_profile.verify_patient_profile_page()
        sa_id = p_profile.verify_patient_profile_details(pfname, plname, mrn, pemail, username, phn, phn_country, default_site_manager, active_account=True, sa_id=True)
        patient_active_account = p_profile.verify_patient_profile_additional_details()
        self.__class__.data.update(
            {"patient_fname": pfname, "patient_lname": plname,
             "patient_email": pemail,
             "patient_phn": phn, "patient_username": username,
             "mrn": mrn, "phone_country": phn_country, "SA_ID": sa_id,
             "site": default_site_manager, "is_patient_active": patient_active_account,

             }
            )

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_patient_3", depends=['tc_patient_2'], scope="class")
    def test_case_03_edit_patient_created_invalid_data(self):
        rerun_count = getattr(self, "rerun_count", 0)
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        profile = UserProfilePage(self, "user")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")
        d = self.__class__.data  # shared dict

        try:
            user_patient.cancel_patient_form()
        except:
            print("Form is already closed")

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
        p_profile.verify_mandatory_fields_with_invalid_data(d["patient_fname"], d["patient_lname"],
                                                                                 d['mrn'],
                                                                                 d["patient_email"],
                                                                                 d['patient_username'],
                                                                                 d["patient_phn"],
                                                                                 d['phone_country'], d['site'],
                                                                                 d['SA_ID']
                                                                                 )

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_patient_4", depends=["tc_patient_3"], scope="class")
    def test_case_04_edit_patient_created_valid_data(self):
        rerun_count = getattr(self, "rerun_count", 0)
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        profile = UserProfilePage(self, "user")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")
        d = self.__class__.data  # shared dict
        try:
            user_patient.cancel_patient_form()
        except:
            print("Form is already closed")
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
        nfname, nlname, nemail = p_profile.edit_mandatory_fields_with_valid_data(d["patient_fname"], d["patient_lname"],
                                                            d['mrn'],
                                                            d["patient_email"],
                                                            d['patient_username'],
                                                            d["patient_phn"],
                                                            d['phone_country'], d['site'],
                                                            d['SA_ID']
                                                            )
        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()

        patient.search_patient(nfname, nlname, d["mrn"], d["patient_username"], d["SA_ID"])

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        self.__class__.data.update(
            {"patient_fname": nfname, "patient_lname": nlname,
             "patient_email": nemail
            }
            )

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_patient_5", depends=["tc_patient_4"], scope="class")
    def test_case_05_edit_patient_indifferent_tabs(self):
        rerun_count = getattr(self, "rerun_count", 0)
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        profile = UserProfilePage(self, "user")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")
        d = self.__class__.data  # shared dict
        try:
            user_patient.cancel_patient_form()
        except:
            print("Form is already closed")

        try:
            login.login(self.settings["login_username"], self.settings["login_password"])
        except Exception:
            print("Not in the login page")
            home.click_admin_profile_button()
            profile.logout_user()
            login.after_logout()
            login.login(self.settings["login_username"], self.settings["login_password"])

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()

        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        patient.open_patient(d["patient_fname"], d["patient_lname"])
        p_profile.load_patient(d["patient_fname"], d["patient_lname"],d['mrn'],
                                                                                 d["patient_email"],
                                                                                 d['patient_username'],
                                                                                 d["patient_phn"],
                                                                                 d['phone_country'], d['site'],
                                                                                 d['SA_ID']
                                                                                 )
        p_profile.inactive_patient()
        p_profile.save_patient_changes()
        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.open_inactive_tab()
        patient.search_patient(d["patient_fname"], d["patient_lname"],d['mrn'], d["patient_username"], d["SA_ID"])
        patient.open_patient(d["patient_fname"], d["patient_lname"])
        p_profile.verify_patient_profile_details(d["patient_fname"], d["patient_lname"],d['mrn'],
                                                 d["patient_email"], d['patient_username'], d["patient_phn"],
                                                 d['phone_country'], d['site'], active_account=False
                                                 )
        p_profile.test_patient(True)
        p_profile.save_patient_changes()

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.login(self.settings["login_username"], self.settings["login_password"])

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.open_test_tab()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        patient.open_patient(d["patient_fname"], d["patient_lname"])
        p_profile.verify_patient_profile_details(d["patient_fname"], d["patient_lname"], d['mrn'],
                                                 d["patient_email"], d['patient_username'], d["patient_phn"],
                                                 d['phone_country'], d['site'], active_account=False, account_test=True
                                                 )
        p_profile.activate_patient(True)
        p_profile.test_patient(False)
        p_profile.save_patient_changes()

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        patient.open_patient(d["patient_fname"], d["patient_lname"])
        p_profile.select_patient_manager(UserData.default_staff_name)
        p_profile.select_treatment_monitor(UserData.default_staff_name)

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.login(self.settings["login_username"], self.settings["login_password"])

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_patient_6", scope="class")
    def test_case_06_global_filter(self):
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        profile = UserProfilePage(self, "user")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")
        d = self.__class__.data  # shared dict

        if "banner" in self.settings["url"] or "rogers" in self.settings["url"]:
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
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
        except Exception:
            home.click_admin_profile_button()
            profile.logout_user()
            login.after_logout()
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()

        try:
            home.clear_filter()
        except:
            print("No Global filters set")

        home.open_manage_patient_page()
        page_count_before = patient.get_total_pages()
        patient.validate_patient_table()
        home.open_filter()
        home.open_filter_search_staff("Sites", default_site_manager, select=True)
        # home.close_filter()
        # home.open_filter()
        home.open_filter_search_staff("Treatment Monitor", UserData.default_staff_name, select=True)
        # home.close_filter()
        # home.open_filter()
        home.open_filter_search_staff("Patient Manager", UserData.default_staff_name, select=True)
        home.close_filter()
        page_count_after = patient.get_total_pages()
        assert page_count_before != page_count_after, f"{page_count_after} is not less than {page_count_before}"
        home.clear_filter()
        assert page_count_before == patient.get_total_pages()

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_patient_7", scope="class")
    def test_case_07_search_patient_sort(self):
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        profile = UserProfilePage(self, "user")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")

        d = self.__class__.data  # shared dict

        try:
            login.login(self.settings["login_username"], self.settings["login_password"])
        except Exception:
            print("Not in the login page")
            home.click_admin_profile_button()
            profile.logout_user()
            login.after_logout()
            login.login(self.settings["login_username"], self.settings["login_password"])


        try:
            home.clear_filter()
        except:
            print("No Global filter is open")

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.search_and_sort_columns("pat_fnmob")

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])
        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.open_inactive_tab()
        patient.validate_inactive_tab()
        patient.search_and_sort_columns("pat_fnmob")

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])
        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.open_test_tab()
        patient.validate_test_tab()
        patient.search_and_sort_columns("pat_fnmob")
