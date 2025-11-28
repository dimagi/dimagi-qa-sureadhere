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


class test_module_06_staff_tests(BaseCase):
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
    @pytest.mark.dependency(name="tc_staff_1", scope="class")
    def test_case_01_add_staff_all_details(self):
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")

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
        fname, lname, email, phn, client, site = user_staff.fill_staff_form(default_site_manager, manager=['PM', 'SM'], login="stf", rerun=rerun_count)
        staff.validate_active_tab()
        staff.search_staff(fname, lname, email, phn,  manager=['PM', 'SM'], site=site)
        self.__class__.data.update({"fname_stf": fname, "lname_stf": lname, "email_stf": email, "phn_stf": phn, "isClientAdmint_stf": client, "site_stf": site})

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_staff_2", scope="class")
    def test_case_02_add_staff_missing_mandatory_fields(self):
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        user_staff = UserStaffPage(self, "add_staff")
        try:
            user_staff.cancel_form()
        except:
            print("Form not present")
        home.click_add_user()
        user.add_staff()
        user_staff.validate_blank_form_submission()

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_staff_3", scope="class")
    def test_case_03_add_staff_without_site_manager(self):
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        user_staff = UserStaffPage(self, "add_staff")
        try:
            user_staff.cancel_form()
        except:
            print("Form not present")
        home.click_add_user()
        user.add_staff()
        user_staff.fill_staff_form_without_site_manager(login="site")

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_staff_4", scope="class")
    @pytest.mark.xfail(reason="Bug #SA3-3589")
    def test_case_04_add_staff_test_account(self):
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")
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
        fname, lname, email, phn, client, site = user_staff.fill_staff_form(default_site_manager, login="test", test_account=True, rerun=rerun_count)
        staff.validate_active_tab()
        home.open_dashboard_page()
        home.open_manage_staff_page()
        staff.open_test_tab()
        staff.search_staff(fname, lname, email, phn, site=site)
        self.__class__.data.update({"fname_test": fname, "lname_test": lname, "email_test": email, "phn_test": phn, "isClientAdmint_test": client, "site_test": site})

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_staff_5", scope="class")
    def test_case_05_duplicate_email_new_staff(self):
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")
        rerun_count = getattr(self, "rerun_count", 0)
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

        home.open_dashboard_page()
        home.click_add_user()
        user.add_staff()
        user_staff.fill_staff_form(default_site_manager, login="test", test_account=True, incorrect='email')


    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_staff_6", depends= ["tc_staff_1"], scope="class")
    def test_case_06_duplicate_email_existing_staff(self):
        self._login_once()
        home = HomePage(self, "dashboard")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")
        try:
            user_staff.cancel_form()
        except:
            print("Form not present")
        home.open_dashboard_page()
        home.open_manage_staff_page()
        staff.validate_manage_staff_page()
        d = self.__class__.data  # shared dict

        staff.search_staff(d["fname_stf"], d["lname_stf"])
        staff.open_staff(d["fname_stf"], d["lname_stf"])
        user_staff.edit_staff_form_with_incorrect_data(d["fname_stf"], d["lname_stf"], email_test=True)

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_staff_7", scope="class")
    def test_case_07_add_staff_invalid_password(self):
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

        try:
            user_staff.cancel_form()
        except:
            print("Form not present")
        home.click_add_user()
        user.add_staff()
        user_staff.fill_staff_form(default_site_manager, login="pwd", incorrect='password')


    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_staff_8", depends= ["tc_staff_1"], scope="class")
    def test_case_08_search_staff(self):
        self._login_once()
        login = LoginPage(self, "login")
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")

        d = self.__class__.data  # shared dict
        try:
            user_staff.cancel_form()
        except:
            print("Form not present")

        try:
            login.validate_login_page()
            login.login(self.settings["login_username"], self.settings["login_password"])
        except Exception:
            print("Login Screen not present")

        home.open_manage_staff_page()
        staff.search_staff_with_partial_info(d['fname_stf'], multiple=3)

        home.open_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff_with_partial_info(d['fname_stf'], caps=True)

        home.open_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff_with_partial_info(d['lname_stf'], multiple=3)

        home.open_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff_with_partial_info(d['lname_stf'], caps=True)

        home.open_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff_with_partial_info(d['fname_stf'],d['lname_stf'], multiple=3)

        home.open_dashboard_page()
        home.open_manage_staff_page()
        staff.search_staff_with_partial_info(d['fname_stf'],d['lname_stf'], caps=True)

    # @pytest.mark.extendedtests
    # @pytest.mark.dependency(name="tc_staff_9", depends=["tc_staff_1"], scope="class")
    # def test_case_09_search_staff_and_sort(self):
    #     self._login_once()
    #     home = HomePage(self, "dashboard")
    #     user = UserPage(self, "add_users")
    #     staff = ManageStaffPage(self, "staff")
    #     user_staff = UserStaffPage(self, "add_staff")
    #
    #     d = self.__class__.data  # shared dict
    #     try:
    #         user_staff.cancel_form()
    #     except:
    #         print("Form not present")
    #     home.open_manage_staff_page()
    #     staff.search_staff_with_partial_info(d['fname_stf'], multiple=3)
    #
    #     home.open_dashboard_page()
    #     home.open_manage_staff_page()
    #     staff.search_staff_with_partial_info(d['fname_stf'], caps=True)