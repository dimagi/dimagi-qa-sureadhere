import random

import pytest
from seleniumbase import BaseCase

from testPages.android.android import Android
from testPages.home_page.home_page import HomePage
from testPages.login_page.login_page import LoginPage

from testPages.manage_patient_page.manage_patient_page import ManagePatientPage
from testPages.patient_tab_pages.patient_adherence_page import PatientAdherencePage
from testPages.patient_tab_pages.patient_messages_page import PatientMessagesPage
from testPages.patient_tab_pages.patient_overview_page import PatientOverviewPage
from testPages.patient_tab_pages.patient_profile_page import PatientProfilePage
from testPages.patient_tab_pages.patient_regimen_page import PatientRegimenPage
from testPages.patient_tab_pages.patient_reports_page import PatientReportsPage
from testPages.patient_tab_pages.patient_video_page import PatientVideoPage
from testPages.user_page.user_page import UserPage
from testPages.user_page.user_patient_page import UserPatientPage

from testPages.user_profile.user_profile_page import UserProfilePage
from user_inputs.user_data import UserData


class test_module_03(BaseCase):
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
        rerun_count = getattr(self, "rerun_count", 0)
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
        start_date, end_date, no_of_pill, med_name, dose_per_pill = p_regimen.create_new_schedule()
        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.search_patient(pfname, plname, mrn,username, sa_id,
                               start_date, end_date, no_of_pill
                               )
        self.__class__.data.update(
            {"patient_fname": pfname, "patient_lname": plname,
             "patient_email": pemail,
             "patient_phn": phn, "patient_username": username,
             "mrn": mrn, "phone_country": phn_country, "SA_ID": sa_id,
             "site": UserData.site_manager[0], "is_patient_active": patient_test_account,
             "patient_pin": patient_pin, "start_date": start_date, "end_date": end_date,
             "total_pills": no_of_pill, "drug_name":med_name, "dose_per_pill": dose_per_pill
             }
            )


    def test_case_01_mobile_login_and_message(self):
        login = LoginPage(self, "login")
        self._login_once()
        mobile = Android(self.settings)
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        patient = ManagePatientPage(self, "patients")
        p_message = PatientMessagesPage(self, 'patient_messagess')

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])

        d = self.__class__.data

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
        vdo_upload_date = mobile.record_video_and_submit(d['drug_name'])
        mobile.close_android_driver()
        self.__class__.data.update(
            {"mob_msg": mob_msg, "web_msg": web_msg, "video_upload_date": vdo_upload_date
             }
            )

    def test_case_02_review_video_and_adherence(self):
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        p_vdo = PatientVideoPage(self, 'patient_video_form')
        p_adhere = PatientAdherencePage(self, 'patient_adherence')

        d = self.__class__.data

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])

        home.validate_dashboard_page()
        home.check_for_quick_actions()
        home.check_for_video_review(d["patient_fname"]+" "+d["patient_lname"], d['SA_ID'])
        p_vdo.verify_patient_video_page()
        formatted_now, review_text=p_vdo.fill_up_review_form(d['drug_name'], d['total_pills'],d['dose_per_pill'])
        p_adhere.verify_patient_adherence_page()
        p_adhere.check_calendar_and_comment_for_adherence(formatted_now, review_text)
        side_effect = p_adhere.fillup_side_effects()
        self.__class__.data.update(
            {"commented_timestamp": formatted_now, "commented_text": review_text, "side_effect": side_effect
             }
            )


    def test_case_03_review_overview(self):
        self._login_once()
        home = HomePage(self, "dashboard")
        p_overview = PatientOverviewPage(self, 'patient_overview')
        patient = ManagePatientPage(self, "patients")

        d = self.__class__.data

        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        patient.open_patient(d["patient_fname"], d["patient_lname"])
        p_overview.open_patient_overview_page()
        p_overview.verify_patient_overview_page()
        p_overview.check_calendar_and_doses(d['commented_timestamp'], d['commented_text'], d['drug_name'], d['start_date'], d['total_pills'])

    def test_case_04_review_reports(self):
        self._login_once()
        home = HomePage(self, "dashboard")
        patient = ManagePatientPage(self, "patients")
        p_report = PatientReportsPage(self, 'patient_reports')

        d = self.__class__.data

        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        patient.open_patient(d["patient_fname"], d["patient_lname"])

        p_report.open_patient_reports_page()
        p_report.verify_patient_reports_page()
        p_report.verify_comment_and_side_effect(d['commented_text'], d['side_effect'])

        p_report.open_patient_reports_page()
        p_report.verify_patient_reports_page()
        p_report.verify_video_report(d['video_upload_date'])



