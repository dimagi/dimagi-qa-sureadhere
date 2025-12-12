import pytest
from pytest_dependency import depends
from seleniumbase import BaseCase

from testPages.home_page.home_page import HomePage
from testPages.login_page.login_page import LoginPage
from testPages.manage_staff_page.manage_staff_page import ManageStaffPage
from testPages.manage_patient_page.manage_patient_page import ManagePatientPage
from testPages.patient_tab_pages.patient_profile_page import PatientProfilePage
from testPages.patient_tab_pages.patient_regimen_page import PatientRegimenPage
from testPages.reports_page.reports_page import ReportsPage
from testPages.user_page.user_page import UserPage
from testPages.user_page.user_patient_page import UserPatientPage
from testPages.user_page.user_staff_page import UserStaffPage
from testPages.user_profile.user_profile_page import UserProfilePage
from user_inputs.user_data import UserData


class test_module_07_staff_manager_roles(BaseCase):
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
    @pytest.mark.dependency(name="tc_staff_role_1", scope="class")
    def test_case_01_validate_role_patient_manager(self):
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        user = UserPage(self, "add_users")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")

        env = self.settings['domain'] if self.settings['domain'] == "rogers" else "others"
        if "banner" in self.settings["url"] or "rogers" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_site_manager = UserData.site_manager[2]
        else:
            default_site_manager = UserData.site_manager[1]

        rerun_count = getattr(self, "rerun_count", 0)
        home.click_add_user()
        user.add_staff()
        fname, lname, email, phn, client, site = user_staff.fill_staff_form(default_site_manager, manager=['PM'], login="sr", rerun=rerun_count)
        staff.validate_active_tab()
        staff.search_staff(fname, lname, email, phn,  manager=['PM'], site=site)

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.validate_login_page()

        login.login(email, UserData.pwd)
        home.validate_dashboard_page()
        home.open_filter()
        home.open_filter_search_staff("Patient Manager", f"{fname} {lname}")
        home.close_filter()
        home.click_add_user()
        user.add_patient()
        pfname, plname, mrn, pemail, username, phn, phn_country = user_patient.fill_patient_form(site,
                                                                                                 rerun_count=rerun_count
                                                                                                 )
        p_profile.verify_patient_profile_page()
        sa_id = p_profile.verify_patient_profile_details(pfname, plname, mrn, pemail, username, phn, phn_country,
                                                         site, sa_id=True
                                                         )
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()

        patient.search_patient(pfname, plname, mrn, username, sa_id)
        patient.open_patient(pfname, plname)
        p_profile.edit_patient_form(fname, lname, pfname, plname, mrn, pemail, username,
                                                                                 phn, phn_country,
                                                                                 site, sa_id, patient_manager=False,
                                                                                 treatment_monitor=False, active_patient=True
                                                                                 )
        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.search_test_patients(UserData.client_1_patient_details[env][0])
        patient.search_test_patients_not_present(UserData.client_2_patient_details[env][0])

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.validate_login_page()

        self.__class__.data.update({"fname_stf": fname, "lname_stf": lname, "email_stf": email, "phn_stf": phn, "isClientAdmint_stf": client, "site_stf": site})

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_staff_role_2", depends=['tc_staff_role_1'], scope="class")
    def test_case_02_validate_role_treatment_monitor(self):
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        user = UserPage(self, "add_users")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")

        d = self.__class__.data  # shared dict

        env = self.settings['domain'] if self.settings['domain'] == "rogers" else "others"

        rerun_count = getattr(self, "rerun_count", 0)
        login.login(self.settings["login_username"], self.settings["login_password"])
        home.validate_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff(d['fname_stf'], d['lname_stf'], d['email_stf'], d['phn_stf'], manager=['PM'], site=d['site_stf'])
        staff.open_staff(d['fname_stf'], d['lname_stf'])
        user_staff.edit_staff_info_options(d['fname_stf'], d['lname_stf'], add_tm=d['site_stf'], remove_managers=['PM', 'SM', 'SS'], client_acc=False)
        user_staff.save_changes()
        home.open_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff(d['fname_stf'], d['lname_stf'], d['email_stf'], d['phn_stf'], manager=['TM'], site=d['site_stf'])

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.validate_login_page()

        login.login(d['email_stf'], UserData.pwd)
        home.validate_dashboard_page()
        home.open_filter()
        home.open_filter_search_staff("Treatment Monitor", f"{d['fname_stf']} { d['lname_stf']}")
        home.close_filter()
        home.click_add_user()
        user.add_patient()
        pfname, plname, mrn, pemail, username, phn, phn_country = user_patient.fill_patient_form(d['site_stf'],
                                                                                                 rerun_count=rerun_count
                                                                                                 )
        p_profile.verify_patient_profile_page()
        sa_id = p_profile.verify_patient_profile_details(pfname, plname, mrn, pemail, username, phn, phn_country,
                                                         d['site_stf'], sa_id=True
                                                         )
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()

        patient.search_patient(pfname, plname, mrn, username, sa_id)
        patient.open_patient(pfname, plname)
        p_profile.edit_patient_form(d['fname_stf'], d['lname_stf'], pfname, plname, mrn, pemail, username,
                                    phn, phn_country,
                                    d['site_stf'], sa_id, patient_manager=False,
                                    treatment_monitor=True, active_patient=True
                                    )
        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.search_test_patients(UserData.client_1_patient_details[env][0])
        patient.search_test_patients_not_present(UserData.client_2_patient_details[env][0])

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.validate_login_page()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_staff_role_3", depends=['tc_staff_role_1', 'tc_staff_role_2'], scope="class")
    def test_case_03_validate_role_site_manager(self):
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        user = UserPage(self, "add_users")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")

        d = self.__class__.data  # shared dict

        env = self.settings['domain'] if self.settings['domain'] == "rogers" else "others"

        rerun_count = getattr(self, "rerun_count", 0)
        login.login(self.settings["login_username"], self.settings["login_password"])
        home.validate_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff(d['fname_stf'], d['lname_stf'], d['email_stf'], d['phn_stf'], manager=['TM'],
                           site=d['site_stf']
                           )
        staff.open_staff(d['fname_stf'], d['lname_stf'])
        user_staff.edit_staff_info_options(d['fname_stf'], d['lname_stf'], add_sm=d['site_stf'],
                                           remove_managers=['PM', 'TM', 'SS'], client_acc=False
                                           )
        user_staff.save_changes()
        home.open_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff(d['fname_stf'], d['lname_stf'], d['email_stf'], d['phn_stf'], manager=['SM'],
                           site=d['site_stf']
                           )

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.validate_login_page()

        login.login(d['email_stf'], UserData.pwd)
        home.validate_dashboard_page()
        home.verify_presence_of_staff_menu(presence=False)
        home.click_add_user()
        user.add_patient()
        pfname, plname, mrn, pemail, username, phn, phn_country = user_patient.fill_patient_form(d['site_stf'],
                                                                                                 rerun_count=rerun_count
                                                                                                 )
        p_profile.verify_patient_profile_page()
        sa_id = p_profile.verify_patient_profile_details(pfname, plname, mrn, pemail, username, phn, phn_country,
                                                         d['site_stf'], sa_id=True
                                                         )
        home.open_manage_patient_page()
        patient.validate_manage_patient_page()

        patient.search_patient(pfname, plname, mrn, username, sa_id)
        patient.open_patient(pfname, plname)
        p_profile.edit_patient_form(d['fname_stf'], d['lname_stf'], pfname, plname, mrn, pemail, username,
                                    phn, phn_country,
                                    d['site_stf'], sa_id, patient_manager=False,
                                    treatment_monitor=False, active_patient=True
                                    )
        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.search_test_patients(UserData.client_1_patient_details[env][0])
        patient.search_test_patients_not_present(UserData.client_2_patient_details[env][0])

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.validate_login_page()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_staff_role_4", depends=['tc_staff_role_1', 'tc_staff_role_2', 'tc_staff_role_3'], scope="class")
    def test_case_04_validate_role_site_staff_admin(self):
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        user = UserPage(self, "add_users")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")

        d = self.__class__.data  # shared dict

        env = self.settings['domain'] if self.settings['domain'] == "rogers" else "others"

        rerun_count = getattr(self, "rerun_count", 0)
        login.login(self.settings["login_username"], self.settings["login_password"])
        home.validate_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff(d['fname_stf'], d['lname_stf'], d['email_stf'], d['phn_stf'], manager=['SM'],
                           site=d['site_stf']
                           )
        staff.open_staff(d['fname_stf'], d['lname_stf'])
        user_staff.edit_staff_info_options(d['fname_stf'], d['lname_stf'], add_ss=d['site_stf'],
                                           remove_managers=['PM', 'TM', 'SM'], client_acc=False
                                           )
        user_staff.save_changes()
        home.open_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff(d['fname_stf'], d['lname_stf'], d['email_stf'], d['phn_stf'], manager=['SM'],
                           site=d['site_stf']
                           )

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.validate_login_page()

        login.login(d['email_stf'], UserData.pwd)
        home.verify_presence_of_staff_menu(presence=True)
        home.verify_presence_of_patient_menu(presence=False)
        home.verify_presence_of_dashboard_menu(presence=False)
        home.verify_presence_of_reports_menu(presence=False)
        home.click_add_user()
        user.add_staff()
        fname, lname, email, phn, client, site = user_staff.fill_staff_form(d['site_stf'], manager=UserData.default_managers, login="ss", rerun=rerun_count)
        staff.validate_active_tab()
        staff.search_staff(fname, lname, email, phn,  manager=UserData.default_managers, site=site)
        staff.open_staff(fname, lname)
        user_staff.verify_presence_of_save_button(presence=False)
        user_staff.cancel_form()

        patient.search_test_patients(UserData.client_1_staff_details[env][0])
        patient.search_test_patients_not_present(UserData.client_2_staff_details[env][0])

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.validate_login_page()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_staff_role_5", depends=['tc_staff_role_1'], scope="class")
    def test_case_05_validate_role_client_staff_admin(self):
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        user = UserPage(self, "add_users")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")

        d = self.__class__.data  # shared dict

        env = self.settings['domain'] if self.settings['domain'] == "rogers" else "others"

        rerun_count = getattr(self, "rerun_count", 0)
        login.login(self.settings["login_username"], self.settings["login_password"])
        home.validate_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff(d['fname_stf'], d['lname_stf'], d['email_stf'], d['phn_stf'],
                           site=d['site_stf']
                           )
        staff.open_staff(d['fname_stf'], d['lname_stf'])
        user_staff.edit_staff_info_options(d['fname_stf'], d['lname_stf'],
                                           remove_managers=['PM', 'TM', 'SM', 'SS'], client_acc=True
                                           )
        user_staff.save_changes()
        home.open_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff(d['fname_stf'], d['lname_stf'], d['email_stf'], d['phn_stf'],
                           site=d['site_stf']
                           )

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.validate_login_page()

        login.login(d['email_stf'], UserData.pwd)
        home.verify_presence_of_staff_menu(presence=True)
        home.verify_presence_of_patient_menu(presence=False)
        home.verify_presence_of_dashboard_menu(presence=False)
        home.verify_presence_of_reports_menu(presence=False)
        home.click_add_user()
        user.add_staff()
        fname, lname, email, phn, client, site = user_staff.fill_staff_form(d['site_stf'], manager=UserData.default_managers, login="ss", rerun=rerun_count)
        staff.validate_active_tab()
        staff.search_staff(fname, lname, email, phn,  manager=UserData.default_managers, site=site)
        staff.open_staff(fname, lname)
        user_staff.verify_presence_of_save_button(presence=True)
        user_staff.edit_staff_info_options(fname, lname, remove_managers=['PM'])
        user_staff.save_changes()
        staff.search_staff(fname, lname, email, phn, site=site)

        patient.search_test_patients(UserData.client_1_staff_details[env][0])
        patient.search_test_patients(UserData.client_2_staff_details[env][0])

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.validate_login_page()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_staff_role_6", depends=['tc_staff_role_1'], scope="class")
    def test_case_06_validate_role_global_data_admin(self):
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        user = UserPage(self, "add_users")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        patient = ManagePatientPage(self, "patients")
        reports = ReportsPage(self, "reports")

        d = self.__class__.data  # shared dict

        env = self.settings['domain'] if self.settings['domain'] == "rogers" else "others"

        rerun_count = getattr(self, "rerun_count", 0)
        login.login(self.settings["login_username"], self.settings["login_password"])
        home.validate_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff(d['fname_stf'], d['lname_stf'], d['email_stf'], d['phn_stf'],
                           site=d['site_stf']
                           )
        staff.open_staff(d['fname_stf'], d['lname_stf'])
        user_staff.edit_staff_info_options(d['fname_stf'], d['lname_stf'],
                                           remove_managers=['PM', 'TM', 'SM', 'SS'], client_acc=False, global_data=True
                                           )
        user_staff.save_changes()
        home.open_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff(d['fname_stf'], d['lname_stf'], d['email_stf'], d['phn_stf'],
                           site=d['site_stf']
                           )

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.validate_login_page()

        login.login(d['email_stf'], UserData.pwd)
        home.verify_presence_of_staff_menu(presence=True)
        home.verify_presence_of_patient_menu(presence=True)
        home.verify_presence_of_dashboard_menu(presence=True)
        home.verify_presence_of_reports_menu(presence=True)

        home.verify_data_table_presence(presence=False)
        home.verify_div_chart_presence(presence=True)

        home.open_filter()
        home.verify_filter_presence("Patient Manager", presence=False)
        home.verify_filter_presence("Treatment Monitor", presence=False)
        home.verify_filter_presence("Disease", presence=False)
        home.verify_filter_presence("Observation method", presence=False)
        home.verify_filter_presence("Site", presence=True)
        home.close_filter()

        home.open_reports_page()
        reports.verify_reports_page()
        reports.validate_report_links(UserData.global_reports)

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        login.validate_login_page()