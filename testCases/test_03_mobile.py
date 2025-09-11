import random

import pytest
from seleniumbase import BaseCase

from testPages.admin_page.admin_disease_page import AdminDiseasePage
from testPages.admin_page.admin_drug_page import AdminDrugPage
from testPages.admin_page.admin_page import AdminPage
from testPages.android.android import Android
from testPages.home_page.home_page import HomePage
from testPages.login_page.login_page import LoginPage
from testPages.manage_staff_page.manage_staff_page import ManageStaffPage
from testPages.manage_patient_page.manage_patient_page import ManagePatientPage
from testPages.patient_tab_pages.patient_adherence_page import PatientAdherencePage
from testPages.patient_tab_pages.patient_messages_page import PatientMessagesPage
from testPages.patient_tab_pages.patient_profile_page import PatientProfilePage
from testPages.patient_tab_pages.patient_regimen_page import PatientRegimenPage
from testPages.patient_tab_pages.patient_video_page import PatientVideoPage
from testPages.user_page.user_page import UserPage
from testPages.user_page.user_patient_page import UserPatientPage
from testPages.user_page.user_staff_page import UserStaffPage
from testPages.user_profile.user_profile_page import UserProfilePage
from user_inputs.user_data import UserData


class test_module_02(BaseCase):
    _session_ready = False  # guard so we only open/login once
    data = {}
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

    @pytest.mark.dependency(name="tc1", scope="class")
    def test_case_00_create_patient(self):
        rerun_count = pytest.request.getfixturevalue("rerun_count")
        # login = LoginPage(self, "login")
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        patient = ManagePatientPage(self, "patients")
        profile = UserProfilePage(self, "user")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        p_regimen = PatientRegimenPage(self, 'patient_regimens')
        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(UserData.default_staff_email, UserData.pwd)
        home.validate_dashboard_page()
        home.click_add_user()
        user.add_patient()
        pfname, plname, mrn, pemail, username, phn, phn_country = user_patient.fill_patient_form(UserData.site_manager[0], mob='YES', rerun_count=rerun_count)
        p_profile.verify_patient_profile_page()
        sa_id = p_profile.verify_patient_profile_details(pfname, plname, mrn, pemail, username, phn, phn_country,
                                                         UserData.site_manager[0], sa_id=True
                                                         )
        p_profile.select_patient_manager(UserData.default_staff_name)
        patient_test_account, patient_pin = p_profile.set_patient_pin(pfname, plname, mrn, pemail,
                                                                      username, phn, phn_country, UserData.site_manager[0]
                                                                      )
        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()
        start_date, end_date, doses, med_name = p_regimen.create_new_schedule()
        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.search_patient(pfname, plname, mrn,username, sa_id,
                               start_date, end_date, doses
                               )
        self.__class__.data.update(
            {"patient_fname": pfname, "patient_lname": plname,
             "patient_email": pemail,
             "patient_phn": phn, "patient_username": username,
             "mrn": mrn, "phone_country": phn_country, "SA_ID": sa_id,
             "site": UserData.site_manager[0], "is_patient_active": patient_test_account,
             "patient_pin": patient_pin, "start_date": start_date, "end_date": end_date,
             "total_dosed": doses, "drug_name":med_name,
             }
            )


    def test_case_01_mobile_login_and_message(self):
        login = LoginPage(self, "login")
        self._login_once()
        mobile = Android(self.settings)
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        patient = ManagePatientPage(self, "patients")
        p_profile = PatientProfilePage(self, 'patient_profile')
        p_message = PatientMessagesPage(self, 'patient_messagess')
        p_vdo = PatientVideoPage(self, 'patient_video_form')
        p_adhere = PatientAdherencePage(self, 'patient_adherence')

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])

        d = self.__class__.data
        print(d['patient_username'])

        home.open_manage_patient_page()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        patient.open_patient(d["patient_fname"], d["patient_lname"])

        mobile.select_environment(self.settings['url'])
        mobile.login_patient(d['patient_username'], d['patient_pin'])
        mob_msg = mobile.send_messages()
        p_message.open_patient_messages_page()
        p_message.verify_patient_messages_page()
        p_message.read_last_message(mob_msg)
        web_msg = p_message.send_message()
        mobile.read_messages(web_msg)
        mobile.record_video_and_submit(d['drug_name'])
        mobile.close_android_driver()
        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])
        home.validate_dashboard_page()
        home.check_for_quick_actions()
        home.check_for_video_review(d["patient_fname"]+" "+d["patient_lname"], d['SA_ID'])
        p_vdo.verify_patient_video_page()
        p_vdo.fill_up_review_form(d['drug_name'])
        p_adhere.verify_patient_adherence_page()



