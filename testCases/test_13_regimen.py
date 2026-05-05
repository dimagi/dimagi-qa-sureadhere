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


class test_module_13_regimen(BaseCase):
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
    @pytest.mark.dependency(name="tc_regimen_01", scope="class")
    def test_case_01_verify_regimen_name(self):
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
        p_adhere = PatientAdherencePage(self, 'patient_adherence')

        if "banner" in self.settings["url"]:
            default_staff_email = UserData.default_staff_email[0]
            default_site_manager = UserData.site_manager[0]
        elif "rogers" in self.settings["url"]:
            default_staff_email = UserData.default_staff_email[1]
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_staff_email = UserData.default_staff_email[3]
            default_site_manager = UserData.site_manager[2]
        else:
            default_staff_email = UserData.default_staff_email[2]
            default_site_manager = UserData.site_manager[1]

        try:
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()
        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.click_add_user()
        user.add_patient()
        pfname, plname, mrn, pemail, username, phn, phn_country = user_patient.fill_patient_form(default_site_manager,
                                                                                                 mob='mob',
                                                                                                 rerun_count=rerun_count
                                                                                                 )
        p_profile.verify_patient_profile_page()
        sa_id = p_profile.verify_patient_profile_details(pfname, plname, mrn, pemail, username, phn, phn_country,
                                                         default_site_manager, sa_id=True
                                                         )
        p_profile.select_patient_manager(UserData.default_staff_name)
        p_profile.select_treatment_monitor(UserData.default_staff_name)
        patient_test_account, patient_pin = p_profile.set_patient_pin(pfname, plname, mrn, pemail,
                                                                      username, phn, phn_country, default_site_manager
                                                                      )
        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()
        reg_name = p_regimen.add_regimen_name()
        p_adhere.open_patient_adherence_page()
        p_adhere.verify_patient_adherence_page()
        p_adhere.verify_regimen_name_presence(reg_name)
        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()
        start_date, end_date, no_of_pill, med_name, dose_per_pill = p_regimen.create_new_schedule(past_date=True, time_of_drug=False)
        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.search_patient(pfname, plname, mrn, username,sa_id,
                               start_date, end_date, no_of_pill
                               )
        self.__class__.data.update(
            {"patient_fname": pfname, "patient_lname": plname,
             "patient_email": pemail,
             "patient_phn": phn, "patient_username": username,
             "mrn": mrn, "phone_country": phn_country, "SA_ID": sa_id,
             "site": default_site_manager, "is_patient_active": patient_test_account,
             "patient_pin": patient_pin, "drug_name": med_name
             }
            )

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_regimen_02", depends=["tc_regimen_01"], scope="class")
    def test_case_02_edit_regimen(self):
        d = self.__class__.data
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
        p_adhere = PatientAdherencePage(self, 'patient_adherence')


        if "banner" in self.settings["url"]:
            default_staff_email = UserData.default_staff_email[0]
            default_site_manager = UserData.site_manager[0]
        elif "rogers" in self.settings["url"]:
            default_staff_email = UserData.default_staff_email[1]
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_staff_email = UserData.default_staff_email[3]
            default_site_manager = UserData.site_manager[2]
        else:
            default_staff_email = UserData.default_staff_email[2]
            default_site_manager = UserData.site_manager[1]

        try:
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()

        home.open_manage_patient_page()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        patient.open_patient(d["patient_fname"], d["patient_lname"])
        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()
        start_date, end_date, no_of_pill, dose_per_pill = p_regimen.edit_schedule(past_date=False, time_of_drug=True, no_of_pills=5, doses=1, repeat=True, end_date=True)
        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"],
                               start_date, end_date, no_of_pill
                               )
        self.__class__.data.update(
            {"start_date": start_date, "end_date": end_date,
             "total_pills": no_of_pill, "dose_per_pill": dose_per_pill}
            )

        @pytest.mark.extendedtests
        @pytest.mark.dependency(name="tc_regimen_03", depends=["tc_regimen_01"], scope="class")
        def test_case_03_multiple_drugs_different_name(self):
            d = self.__class__.data
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
            p_adhere = PatientAdherencePage(self, 'patient_adherence')

            if "banner" in self.settings["url"]:
                default_staff_email = UserData.default_staff_email[0]
                default_site_manager = UserData.site_manager[0]
            elif "rogers" in self.settings["url"]:
                default_staff_email = UserData.default_staff_email[1]
                default_site_manager = UserData.site_manager[0]
            elif "securevoteu" in self.settings["url"]:
                default_staff_email = UserData.default_staff_email[3]
                default_site_manager = UserData.site_manager[2]
            else:
                default_staff_email = UserData.default_staff_email[2]
                default_site_manager = UserData.site_manager[1]

            try:
                home.open_dashboard_page()
                home.validate_dashboard_page()
            except Exception:
                login.login(self.settings["login_username"], self.settings["login_password"])
                home.open_dashboard_page()
                home.validate_dashboard_page()

            home.open_manage_patient_page()
            patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
            patient.open_patient(d["patient_fname"], d["patient_lname"])
            p_regimen.open_patient_regimen_page()
            p_regimen.verify_patient_regimen_page()
            start_date, end_date, no_of_pill, med_name, dose_per_pill=p_regimen.create_new_schedule(disease_flag=False, past_date=False,time_of_drug=True, donot_add_drug=d['drug_name'])
            # start_date, end_date, no_of_pill, dose_per_pill = p_regimen.edit_schedule(past_date=False,
            #                                                                           time_of_drug=True, no_of_pills=5,
            #                                                                           doses=1, repeat=True,
            #                                                                           end_date=True
            #                                                                           )

            self.__class__.data.update(
                {"start_date_2": start_date, "end_date_2": end_date,
                 "total_pills_2": no_of_pill, "dose_per_pill_2": dose_per_pill, "drug_name_2": med_name}
                )

    @pytest.mark.extendedtests
    @pytest.mark.dependency(name="tc_regimen_04", depends=["tc_regimen_01"], scope="class")
    def test_case_04_multiple_drugs_same_name(self):
        d = self.__class__.data
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
        p_adhere = PatientAdherencePage(self, 'patient_adherence')

        if "banner" in self.settings["url"]:
            default_staff_email = UserData.default_staff_email[0]
            default_site_manager = UserData.site_manager[0]
        elif "rogers" in self.settings["url"]:
            default_staff_email = UserData.default_staff_email[1]
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_staff_email = UserData.default_staff_email[3]
            default_site_manager = UserData.site_manager[2]
        else:
            default_staff_email = UserData.default_staff_email[2]
            default_site_manager = UserData.site_manager[1]

        try:
            home.open_dashboard_page()
            home.validate_dashboard_page()
        except Exception:
            login.login(self.settings["login_username"], self.settings["login_password"])
            home.open_dashboard_page()
            home.validate_dashboard_page()

        home.open_manage_patient_page()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        patient.open_patient(d["patient_fname"], d["patient_lname"])
        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()
        p_regimen.delete_schedule()
        start_date, end_date, no_of_pill, med_name, dose_per_pill = p_regimen.create_new_schedule(past_date=True,
                                                                                                  time_of_drug=False
                                                                                                  )
        start_date_2, end_date_2, no_of_pill_2, med_name_2, dose_per_pill_2 = p_regimen.create_new_schedule(past_date=False,
                                                                                                  time_of_drug=True,
                                                                                                  drug_name=med_name
                                                                                                  )


        self.__class__.data.update(
            {"start_date": start_date, "end_date": end_date,
             "total_pills": no_of_pill, "dose_per_pill": dose_per_pill, "drug_name": med_name,
             "start_date_2": start_date_2, "end_date_2": end_date_2,
             "total_pills_2": no_of_pill_2, "dose_per_pill_2": dose_per_pill_2, "drug_name_2": med_name_2
             }
            )