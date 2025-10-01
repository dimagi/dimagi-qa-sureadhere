import random
import time

import pytest
from seleniumbase import BaseCase

from testPages.admin_page.admin_announcement_form_page import AdminAnnouncementFormPage
from testPages.admin_page.admin_announcement_page import AdminAnnouncementPage
from testPages.admin_page.admin_disease_page import AdminDiseasePage
from testPages.admin_page.admin_drug_page import AdminDrugPage
from testPages.admin_page.admin_ff_page import AdminFFPage
from testPages.admin_page.admin_page import AdminPage
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


class test_module_00_presetup(BaseCase):

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

    @pytest.mark.presetup
    @pytest.mark.order(1)  # ensure this test runs first
    @pytest.mark.dependency(name="presetup")
    @pytest.mark.run_on_main_process
    def test_case_00_ff_pre_setup(self):
        # login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        admin = AdminPage(self, 'admin')
        a_ff = AdminFFPage(self, 'feature_flags')


        if "banner" in self.settings["url"] or "rogers" in self.settings["url"]:
            default_client = UserData.client[0]
        elif "secure" in self.settings["url"]:
            default_client = UserData.client[1]
        else:
            default_client = UserData.client[2]

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.set_ffs(UserData.ff)
        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.double_check_ff(UserData.ff)
