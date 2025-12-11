import pytest
from pytest_dependency import depends
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

        try:
            user_staff.cancel_form()
        except:
            print("Form not present")

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

        # pfname, plname, mrn, pemail, username, phn, phn_country = user_patient.fill_patient_form(d['site'],
        #                                                                                          rerun_count=rerun_count
        #                                                                                          )
        # p_profile.verify_patient_profile_page()
        # sa_id = p_profile.verify_patient_profile_details(pfname, plname, mrn, pemail, username, phn, phn_country,
        #                                                  site, sa_id=True
        #                                                  )

        self.__class__.data.update({"fname_stf": fname, "lname_stf": lname, "email_stf": email, "phn_stf": phn, "isClientAdmint_stf": client, "site_stf": site})

