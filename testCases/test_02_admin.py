import random
import time

import pytest
from seleniumbase import BaseCase

from testPages.admin_page.admin_announcement_form_page import AdminAnnouncementFormPage
from testPages.admin_page.admin_announcement_page import AdminAnnouncementPage
from testPages.admin_page.admin_disease_page import AdminDiseasePage
from testPages.admin_page.admin_drug_page import AdminDrugPage
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


class test_module_02_admin(BaseCase):
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
    @pytest.mark.dependency(name="tc_admin_1", scope="class")
    def test_case_01_edit_disease_and_drugs(self):
        # login = LoginPage(self, "login")
        self._login_once()
        a_disease = AdminDiseasePage(self, 'admin_diseases')
        home = HomePage(self, "dashboard")
        admin = AdminPage(self, 'admin')
        a_drug = AdminDrugPage(self, 'admin_drugs')

        selected_disease = random.choice(UserData.admin_disease)
        selected_drug = random.choice(UserData.admin_drug)

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.expand_diseases()
        disease_switch, disease_name = a_disease.toggle_for_disease(selected_disease)

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.expand_diseases()
        a_disease.double_check_on_toggle(disease_name, disease_switch)

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.expand_drugs()
        drug_switch, drug_name = a_drug.toggle_for_drugs(selected_drug)

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.expand_drugs()
        a_drug.double_check_on_toggle(drug_name, drug_switch)

        self.__class__.data.update(
            {"disease_switch": disease_switch, "disease_name": disease_name,
             "drug_switch": drug_switch, "drug_name": drug_name}
            )

    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_admin_2", depends=['tc_admin_1'] ,scope="class")
    def test_case_02_verify_disease_and_drugs(self):
        # login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        admin =AdminPage(self, 'admin')
        a_disease = AdminDiseasePage(self, 'admin_diseases')
        a_drug = AdminDrugPage(self, 'admin_drugs')
        patient = ManagePatientPage(self, "patients")
        p_regimen = PatientRegimenPage(self, 'patient_regimens')

        d = self.__class__.data


        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.search_test_patients()
        patient.open_first_patient()
        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()
        p_regimen.verify_diseases_present(d['disease_name'], d['disease_switch'])

        home.open_dashboard_page()
        home.open_manage_patient_page()
        patient.search_test_patients()
        patient.open_first_patient()
        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()
        p_regimen.verify_drugs_present(d['drug_name'], d['drug_switch'])

        home.open_dashboard_page()
        home.open_admin_page()
        admin.expand_diseases()
        disease_switch_now, disease_name = a_disease.toggle_for_disease(d['disease_name'])

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.expand_diseases()
        a_disease.double_check_on_toggle(disease_name, disease_switch_now)

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.expand_drugs()
        drug_switch_now, drug_name = a_drug.toggle_for_drugs(d['drug_name'])

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.expand_drugs()
        a_drug.double_check_on_toggle(drug_name, drug_switch_now)


        home.open_dashboard_page()
        print(f"Before: {d['disease_switch']}, Drug Name: {disease_name}, After: {disease_switch_now}")

        print("sleeping for the changes to reflect...")
        time.sleep(30)

        home.open_manage_patient_page()
        patient.search_test_patients()
        patient.open_first_patient()
        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()
        p_regimen.verify_diseases_present(disease_name, disease_switch_now)

        home.open_dashboard_page()
        print(f"Before: {d['drug_switch']}, Drug Name: {d['drug_name']}, After: {drug_switch_now}")
        home.open_manage_patient_page()
        patient.search_test_patients()
        patient.open_first_patient()
        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()
        p_regimen.verify_drugs_present(drug_name, drug_switch_now)

    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_admin_3", scope="class")
    def test_case_01_edit_disease_and_verify(self):
        # login = LoginPage(self, "login")
        self._login_once()

        home = HomePage(self, "dashboard")
        admin = AdminPage(self, 'admin')
        a_announce = AdminAnnouncementPage(self, 'announcements')
        a_announce_form = AdminAnnouncementFormPage(self, 'admin_announcement_form')

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_admin_page()
        admin.open_announcement()
        a_announce.verify_announcements_page()
        a_announce.add_announcement()
        a_announce_form.validate_announcement_page()
        announcement_text, status, client = a_announce_form.add_announcement()
        home.open_admin_page()
        admin.open_announcement()
        a_announce.verify_announcement_created(announcement_text, status, client)
        home.open_dashboard_page()
        home.verify_announcement(announcement_text)
        client = UserData.client

        home.open_admin_page()
        admin.open_announcement()
        a_announce.edit_announcement(announcement_text)
        a_announce_form.validate_announcement_page()
        status_now = a_announce_form.deactivate_the_announcements()
        home.open_admin_page()
        admin.open_announcement()
        a_announce.verify_announcement_created(announcement_text, status_now)

