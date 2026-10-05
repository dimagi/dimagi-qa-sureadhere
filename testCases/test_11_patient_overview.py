import pytest
from pytest_dependency import depends
from seleniumbase import BaseCase

from testPages.admin_page.admin_disease_page import AdminDiseasePage
from testPages.admin_page.admin_drug_page import AdminDrugPage
from testPages.admin_page.admin_ff_page import AdminFFPage
from testPages.admin_page.admin_page import AdminPage
from testPages.android.android import Android
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
from testPages.patient_tab_pages.patient_video_page import PatientVideoPage
from testPages.user_page.user_page import UserPage
from testPages.user_page.user_patient_page import UserPatientPage
from testPages.user_profile.user_profile_page import UserProfilePage
from user_inputs.user_data import UserData


class test_module_11_patient_overview(BaseCase):
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
    @pytest.mark.dependency(name="tc_pat_overview_01", scope="class")
    def test_case_01_overview_before_regimen(self):
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
        p_overview = PatientOverviewPage(self, 'patient_overview')

        if "banner" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "rogers" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_site_manager = UserData.site_manager[2]
        else:
            default_site_manager = UserData.site_manager[1]

        try:
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()


        home.click_add_user()
        user.add_patient()
        fname, lname, mrn, pemail, username, phn, phn_country = user_patient.fill_patient_form(default_site_manager,
                                                                                                 mob='ov',
                                                                                                 rerun_count=rerun_count
                                                                                                 )
        p_profile.verify_patient_profile_page()
        sa_id = p_profile.verify_patient_profile_details(fname, lname, mrn, pemail, username, phn, phn_country,
                                                         default_site_manager, sa_id=True
                                                         )
        p_profile.select_patient_manager(UserData.default_staff_name)
        p_profile.select_treatment_monitor(UserData.default_staff_name)
        p_profile.save_patient_changes()
        patient_test_account, patient_pin = p_profile.set_patient_pin(fname, lname, mrn, pemail,
                                                                      username, phn, phn_country, default_site_manager
                                                                      )
        p_overview.open_patient_overview_page()
        p_overview.verify_patient_overview_page()
        p_overview.check_calendar_presence()
        p_overview.check_doses_table_before()

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        self.__class__.data.update(
            {"patient_fname": fname, "patient_lname": lname,
             "patient_email": pemail,
             "patient_phn": phn, "patient_username": username,
             "mrn": mrn, "phone_country": phn_country, "SA_ID": sa_id,
             "site": default_site_manager, "patient_pin": patient_pin,
             }
            )

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_overview_02",depends=['tc_pat_overview_01'] , scope="class")
    def test_case_02_overview_after_regimen(self):
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
        p_overview = PatientOverviewPage(self, 'patient_overview')
        mobile = Android(self.settings)
        p_vdo = PatientVideoPage(self, 'patient_video_form')
        p_adhere = PatientAdherencePage(self, 'patient_adherence')

        d = self.__class__.data

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
        p_regimen.verify_patient_regimen_page()
        if rerun_count != 0:
            p_regimen.delete_schedule()
        start_date, end_date, no_of_pill, med_name, dose_per_pill = p_regimen.create_new_schedule()

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        mobile.select_environment(self.settings['url'])
        mobile.login_patient(d['patient_username'], d['patient_pin'])
        vdo_upload_date, vdo_upload_time = mobile.record_video_and_submit(med_name)
        mobile.close_android_driver()

        login.login(self.settings["login_username"], self.settings["login_password"])
        home.open_dashboard_page()

        home.validate_dashboard_page()
        home.check_for_quick_actions()
        home.check_for_video_review(d["patient_fname"] + " " + d["patient_lname"], d['SA_ID'])
        p_vdo.verify_patient_video_page()
        now, formatted_now, review_text = p_vdo.fill_up_review_form(med_name, no_of_pill,
                                                                    dose_per_pill
                                                                    )
        p_adhere.verify_patient_adherence_page()
        p_adhere.check_calendar_and_comment_for_adherence(now, formatted_now, review_text)
        side_effect = p_adhere.fillup_side_effects()
        p_vdo.close_form()
        p_overview.open_patient_overview_page()
        p_overview.verify_patient_overview_page()
        p_overview.check_calendar_and_doses(formatted_now, review_text, med_name,
                                            start_date, no_of_pill
                                            )

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        self.__class__.data.update(
            {"start_date": start_date, "end_date": end_date,
             "total_pills": no_of_pill, "drug_name":med_name, "dose_per_pill": dose_per_pill,
             "commented_timestamp": formatted_now, "commented_text": review_text, "side_effect": side_effect
             }
            )

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_pat_overview_03", depends = ['tc_pat_overview_01', 'tc_pat_overview_02'], scope="class")
    def test_case_03_overview_charts(self):
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
        p_overview = PatientOverviewPage(self, 'patient_overview')
        p_adhere = PatientAdherencePage(self, 'patient_adherence')

        d = self.__class__.data

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

        p_overview.open_patient_overview_page()
        p_overview.verify_patient_overview_page()
        p_overview.check_pie_chart()

        p_overview.export_pdf(fname=d['patient_fname'], lname=d['patient_lname'], mrn=d['mrn'])
        value = p_overview.click_any_date()

        p_adhere.verify_patient_adherence_page()
        p_adhere.verify_selected_date(value)
        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
