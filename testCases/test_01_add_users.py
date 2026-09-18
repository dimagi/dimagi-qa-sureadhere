import pytest
from seleniumbase import BaseCase

from common_utilities.perf import perf_budget
from common_utilities.step_reporter import checklist_step, report_values, wait_for_step
from testPages.admin_page.admin_ff_page import AdminFFPage
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


class test_module_01_users(BaseCase):
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

    @pytest.mark.testcase("https://docs.google.com/spreadsheets/d/1EE2S3J4i964P_C-FCFxxHUYNxK3iP6XEoyKVoeWvZzs/edit?gid=530160723#gid=530160723&range=A8:J8")
    @pytest.mark.tcid("new_entities_1")
    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_users_1", scope="class")
    def test_case_01_add_staff(self):
        # login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")
        login = LoginPage(self, "login")
        if "banner" in self.settings["url"] or "rogers" in self.settings["url"]:
            default_site_manager = UserData.site_manager[0]
        elif "securevoteu" in self.settings["url"]:
            default_site_manager = UserData.site_manager[2]
        else:
            default_site_manager = UserData.site_manager[1]
        rerun_count = getattr(self, "rerun_count", 0)
        try:
            user_staff.cancel_form()
        except:
            print("Form is already closed")

        with checklist_step("login_existing_staff"):
            report_values({"admin_username": self.settings["login_username"]})
            home.ensure_logged_in()

        home.click_add_user()
        user.add_staff()
        with checklist_step("staff_created"):
            fname, lname, email, phn, client, site = user_staff.fill_staff_form(default_site_manager, rerun=rerun_count)
            report_values({"new_staff_username": email})
        staff.validate_manage_staff_page()
        staff.search_staff(fname, lname, email, phn)
        home.click_admin_profile_button()
        profile = UserProfilePage(self, "user")
        profile.logout_user()
        login.after_logout()
        self.__class__.data.update({"fname": fname, "lname": lname, "email": email, "phn": phn, "isClientAdmint": client, "site": site})
        print(self.data)


    @pytest.mark.testcase(
        "https://docs.google.com/spreadsheets/d/1EE2S3J4i964P_C-FCFxxHUYNxK3iP6XEoyKVoeWvZzs/edit?gid=530160723#gid=530160723&range=A9:J9"
        )
    @pytest.mark.tcid("new_entities_2")
    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_users_2", depends=["tc_users_1"], scope="class")
    def test_case_02_edit_staff(self):
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        staff = ManageStaffPage(self, "staff")
        user_staff = UserStaffPage(self, "add_staff")

        home.ensure_logged_in()

        home.open_manage_staff_page()
        staff.validate_manage_staff_page()
        d = self.__class__.data  # shared dict

        with checklist_step("staff_edited"):
            staff.search_staff(d["fname"], d["lname"], d["email"], d["phn"])
            staff.open_staff(d["fname"], d["lname"])
            new_fname, new_lname, account_active, test_account=user_staff.edit_staff_form(d["fname"], d["lname"], d["email"], d["phn"], client=d["isClientAdmint"])
            home.open_dashboard_page()
            home.open_manage_staff_page()
            staff.validate_manage_staff_page()
            if account_active == False:
                staff.open_inactive_tab()
            elif test_account == True:
                staff.open_test_tab()
            staff.search_staff(new_fname, new_lname, d["email"], d["phn"])
            staff.open_staff(new_fname, new_lname)
            user_staff.wait_for_staff_to_load(new_fname, new_lname)
            user_staff.verify_basic_staff_data(new_fname, new_lname, d["email"], d["phn"], client=d["isClientAdmint"], active=account_active, test=test_account)
            user_staff.make_staff_active(new_fname, new_lname, d["email"], d["phn"])
        home.click_admin_profile_button()
        profile = UserProfilePage(self, "user")
        profile.logout_user()
        login.after_logout()
        self.__class__.data.update(
            {"fname": new_fname, "lname": new_lname, "isActive": account_active, "isTest": test_account}
            )
        print(self.data)

    @pytest.mark.testcase(
        "https://docs.google.com/spreadsheets/d/1EE2S3J4i964P_C-FCFxxHUYNxK3iP6XEoyKVoeWvZzs/edit?gid=530160723#gid=530160723&range=A10:J10"
        )
    @pytest.mark.tcid("new_entities_3")
    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_users_3", depends=["tc_users_1", "tc_users_2"], scope="class")
    def test_case_03_login_new_staff_and_create_patient(self):
        rerun_count = getattr(self, "rerun_count", 0)
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        user = UserPage(self, "add_users")
        profile = UserProfilePage(self, "user")
        user_patient = UserPatientPage(self, "add_patient")
        p_profile = PatientProfilePage(self, 'patient_profile')
        d = self.__class__.data
        try:
            user_patient.cancel_patient_form()
        except:
            print("Form is already closed")
        try:
            home.click_admin_profile_button()
            profile.logout_user()
            login.after_logout()
        except:
            print("Already logged out")
        with checklist_step("login_new_staff"):
            login.login(d["email"], UserData.pwd)
            home.validate_dashboard_page()
        home.click_add_user()
        user.add_patient()
        with checklist_step("patient_created"), perf_budget("create_patient"):
            pfname, plname, mrn, pemail, username, phn, phn_country = user_patient.fill_patient_form(d['site'], rerun_count=rerun_count)
            p_profile.verify_patient_profile_page()
            sa_id = p_profile.verify_patient_profile_details(pfname, plname, mrn, pemail, username, phn, phn_country, d['site'], sa_id=True)
            report_values({"admin_patient_sa_id": sa_id})
        self.__class__.data.update(
            {"patient_fname": pfname, "patient_lname": plname,
             "patient_email": pemail,
             "patient_phn": phn, "patient_username": username,
             "mrn": mrn, "phone_country":phn_country, "SA_ID": sa_id})
        home.click_admin_profile_button()
        profile = UserProfilePage(self, "user")
        profile.logout_user()
        login.after_logout()

    @pytest.mark.testcase(
        "https://docs.google.com/spreadsheets/d/1EE2S3J4i964P_C-FCFxxHUYNxK3iP6XEoyKVoeWvZzs/edit?gid=530160723#gid=530160723&range=A11:J11"
        )
    @pytest.mark.tcid("new_entities_4")
    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_users_4", depends=["tc_users_1", "tc_users_2", "tc_users_3"], scope="class")
    def test_case_04_patient_edited(self):
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        staff = ManageStaffPage(self, "staff")
        patient = ManagePatientPage(self, "patients")
        p_profile = PatientProfilePage(self, 'patient_profile')

        d = self.__class__.data  # shared dict
        home.ensure_logged_in()

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()

        with checklist_step("patient_edited"):
            patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
            patient.open_patient(d["patient_fname"], d["patient_lname"])
            new_fname, new_lname, patient_test_account=p_profile.edit_patient_form(d['fname'], d['lname'],
                d["patient_fname"], d["patient_lname"], d['mrn'],
                d["patient_email"], d['patient_username'], d["patient_phn"],
                d['phone_country'], d['site'], d['SA_ID']
                )

            home.open_dashboard_page()
            home.validate_dashboard_page()
            home.open_manage_patient_page()
            patient.open_inactive_tab()
            patient.search_patient(new_fname, new_lname, d["mrn"], d["patient_username"], d["SA_ID"])
            patient.open_patient(new_fname, new_lname)
            p_profile.verify_patient_profile_details(new_fname, new_lname, d['mrn'],
                d["patient_email"], d['patient_username'], d["patient_phn"],
                d['phone_country'], d['site'], active_account=patient_test_account)
        self.__class__.data.update(
            {"patient_fname": new_fname, "patient_lname": new_lname,
             "is_patient_active": patient_test_account}
            )
        home.click_admin_profile_button()
        profile = UserProfilePage(self, "user")
        profile.logout_user()
        login.after_logout()

    @pytest.mark.testcase(
        "https://docs.google.com/spreadsheets/d/1EE2S3J4i964P_C-FCFxxHUYNxK3iP6XEoyKVoeWvZzs/edit?gid=530160723#gid=530160723&range=A12:J12"
        )
    @pytest.mark.tcid("new_entities_5")
    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_users_5", depends=["tc_users_1", "tc_users_2", "tc_users_3", "tc_users_4"], scope="class")
    def test_case_05_patient_pin_generated(self):
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        staff = ManageStaffPage(self, "staff")
        patient = ManagePatientPage(self, "patients")
        p_profile = PatientProfilePage(self, 'patient_profile')

        d = self.__class__.data  # shared dict
        home.ensure_logged_in()

        home.open_manage_patient_page()
        patient.validate_manage_patient_page()
        patient.open_inactive_tab()
        with checklist_step("patient_pin_generated"):
            patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
            patient.open_patient(d["patient_fname"], d["patient_lname"])
            patient_test_account, patient_pin=p_profile.set_patient_pin(d["patient_fname"], d["patient_lname"], d['mrn'],
                d["patient_email"], d['patient_username'], d["patient_phn"],
                d['phone_country'], d['site']
                )
        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        self.__class__.data.update(
            {"is_patient_active": patient_test_account, "patient_pin": patient_pin }
            )
        home.click_admin_profile_button()
        profile = UserProfilePage(self, "user")
        profile.logout_user()
        login.after_logout()

    @pytest.mark.testcase(
        "https://docs.google.com/spreadsheets/d/1EE2S3J4i964P_C-FCFxxHUYNxK3iP6XEoyKVoeWvZzs/edit?gid=530160723#gid=530160723&range=A13:J13"
        )
    @pytest.mark.tcid("new_entities_6_new")
    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_users_6", depends=["tc_users_1", "tc_users_2", "tc_users_3", "tc_users_4", "tc_users_5"], scope="class")
    def test_case_06_regimen_created_and_edited(self):
        self._login_once()
        home = HomePage(self, "dashboard")
        staff = ManageStaffPage(self, "staff")
        patient = ManagePatientPage(self, "patients")
        p_profile = PatientProfilePage(self, 'patient_profile')
        p_regimen = PatientRegimenPage(self, 'patient_regimens')

        d = self.__class__.data  # shared dict

        home.force_relogin()

        home.open_manage_patient_page()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        patient.open_patient(d["patient_fname"], d["patient_lname"])
        p_regimen.open_patient_regimen_page()
        p_regimen.verify_patient_regimen_page()
        with checklist_step("regimen_created"), perf_budget("create_regimen"):
            start_date, end_date, no_of_pill, med_name, dose_per_pill = p_regimen.create_new_schedule()

        home.force_relogin()

        with checklist_step("regimen_edited"), perf_budget("edit_regimen"):
            home.open_manage_patient_page()
            patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
            patient.open_patient(d["patient_fname"], d["patient_lname"])
            p_regimen.open_patient_regimen_page()
            p_regimen.verify_patient_regimen_page()
            # create_new_schedule() was called with no explicit no_of_pills/doses
            # override above, so it used UserData's defaults; its 5th return
            # value is the *total* dose (pills * dose_per_pill), not the
            # per-pill dose other callers of this tuple need it to be (see
            # PatientVideoPage.fill_up_review_form_ff_on/off's "Xmg/Ypills"
            # text, which matches the real UI showing total dose there) --
            # pass the real per-pill value directly instead of that field.
            # end_date=True: without it, edit_schedule() never touches the
            # end-date field and the edited schedule collapses to a single
            # day (start == end), which is what caused the calendar
            # verification inside edit_schedule() to find every day after
            # the start date missing its dot.
            p_regimen.edit_schedule(med_name, no_of_pills=no_of_pill, doses=UserData.dose_per_pill, end_date=True)

        home.validate_dashboard_page()
        home.open_manage_patient_page()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"], start_date, end_date, no_of_pill)
        self.__class__.data.update(
            {"start_date": start_date, "end_date": end_date,
             "total_pills": no_of_pill, "drug_name":med_name, "dose_per_pill": dose_per_pill}
            )
        print(self.data)

    @pytest.mark.tcid("mobile_and_web_1, mobile_and_web_2, mobile_and_web_3, mobile_and_web_4")
    @pytest.mark.smoketest
    @pytest.mark.dependency(name="tc_users_7",
                            depends=["tc_users_1", "tc_users_2", "tc_users_3", "tc_users_4", "tc_users_5", "tc_users_6"],
                            scope="session")
    def test_case_07_add_video_to_second_patient(self):
        rerun_count = getattr(self, "rerun_count", 0)
        login = LoginPage(self, "login")
        self._login_once()
        self.mobile = Android(self.settings)
        mobile = self.mobile
        home = HomePage(self, "dashboard")
        profile = UserProfilePage(self, "user")
        patient = ManagePatientPage(self, "patients")
        p_message = PatientMessagesPage(self, 'patient_messagess')

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        login.login(self.settings["login_username"], self.settings["login_password"])

        d = self.__class__.data

        home.open_dashboard_page()
        home.validate_dashboard_page()
        home.open_dashboard_page()
        home.check_for_quick_actions()
        flag = home.check_for_review_presence(d["patient_fname"] + " " + d["patient_lname"], d['SA_ID'])

        home.open_manage_patient_page()
        patient.search_patient(d["patient_fname"], d["patient_lname"], d["mrn"], d["patient_username"], d["SA_ID"])
        patient.open_patient(d["patient_fname"], d["patient_lname"])

        with checklist_step("mobile_login"):
            report_values({"device_type": "Google Pixel 9 (Android)"})
            mobile.select_environment(self.settings['url'])
            mobile.login_patient(d['patient_username'], d['patient_pin'])

        with checklist_step("video_submitted"):
            if flag == False:
                with perf_budget("mobile_video_submit"):
                    vdo_upload_date, vdo_upload_time = mobile.record_video_and_submit(d['drug_name'], d["total_pills"])
                # Self-report submits the same data the video wizard already records for this
                # dose; calling both creates duplicate self-report events for the same dose,
                # which the matcher treats as ambiguous ("multiple covering reports") and
                # suppresses the auto-filled tag entirely.
                # mobile.self_report_and_submit(d['drug_name'], d["total_pills"])
                mobile.close_android_driver()
                self.__class__.data.update({
                    "video_upload_date": vdo_upload_date,
                    "video_upload_time": vdo_upload_time,
                })
            else:
                print("video already uploaded")
                vdo_upload_date = d.get("video_upload_date")
                vdo_upload_time = d.get("video_upload_time")
        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()
        self.__class__.data.update(
            {"video_upload_date": vdo_upload_date,
             "video_upload_time": vdo_upload_time
             }
        )
        # The Slack checklist labels for the steps test_case_08 reports
        # (auto_complete_self_report / dose_submitted_pda_off) show this
        # patient's SA-ID -- report_values() is the only cross-worker path
        # for that (conftest.py's pytest_terminal_summary renders the report
        # from a different process), even though test_case_08 itself reads
        # this patient's data straight from self.__class__.data since it's
        # in the same class.
        report_values({"patient2_sa_id": d["SA_ID"]})

    @pytest.mark.tcid("mobile_and_web_5, mobile_and_web_6")
    @pytest.mark.smoketest
    # "tc_mobile_3_on" deliberately left out of depends=[...]: pytest-dependency
    # tracks results per xdist worker process, and tc_mobile_3_on (test_case_02a)
    # runs in test_03_mobile.py's worker, a different process from this one --
    # so this worker never sees it recorded as passed even when it genuinely
    # has finished, causing an instant, incorrect skip (confirmed via a real
    # run: tc_mobile_3_on passed at 09:31:52, this test still got skipped at
    # 09:35:09 with reason "depends on tc_mobile_3_on"). wait_for_step() below
    # -- which polls the real shared per-environment file instead of relying on
    # pytest-dependency's per-worker registry -- is what actually enforces
    # that ordering correctly.
    @pytest.mark.dependency(name="tc_users_8", depends=["tc_users_7"], scope="class")
    @pytest.mark.flaky(reruns=0)
    def test_case_08_dose_submitted_pda_disabled_and_auto_complete_self_report(self):
        # No automatic rerun (see @pytest.mark.flaky(reruns=0) above): the
        # rerun_count != 0 branch this test used to have took a shorter
        # navigation path straight into the dose-status check, without the
        # fuller page-load verification the first-attempt path does --
        # confirmed as the real cause of a live failure ("No working locator
        # found for 'doseStatus'": the Adherence page was still showing its
        # loading spinner). Same fix as test_case_02a: always take the one,
        # fully-verified path instead of a rerun-only shortcut that can hit
        # the page before it's ready.
        login = LoginPage(self, "login")
        self._login_once()
        home = HomePage(self, "dashboard")
        p_vdo = PatientVideoPage(self, 'patient_video_form')
        p_adhere = PatientAdherencePage(self, 'patient_adherence')
        profile = UserProfilePage(self, "user")
        a_ff = AdminFFPage(self, 'feature_flags')
        admin = AdminPage(self, 'admin')

        # test_case_02a (test_03_mobile.py) runs in a different xdist worker
        # process and toggles the same environment-wide Per Drug Adherence
        # flag ON -- pytest-dependency's depends=[...] above can't reliably
        # block on it across processes, so wait on the shared per-environment
        # step file directly before flipping that same flag OFF here.
        wait_for_step("dose_submitted_pda_on")
        d = self.__class__.data

        if "banner" in self.settings["url"]:
            default_client = UserData.client[0]
        elif "rogers" in self.settings["url"]:
            default_client = UserData.client[1]
        elif "securevoteu" in self.settings["url"]:
            default_client = UserData.client[3]
        else:
            default_client = UserData.client[2]
        home.force_relogin()

        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.set_ffs(UserData.per_drug_adherence_ff_off)

        home.open_dashboard_page()
        # home.validate_dashboard_page()
        home.open_admin_page()
        admin.open_feature_flags()
        a_ff.validate_admin_ff_page(default_client)
        a_ff.double_check_ff(UserData.per_drug_adherence_ff_off)

        home.force_relogin()

        def _review_video_and_verify_adherence():
            p_vdo.verify_patient_video_page()
            flag = p_vdo.check_for_video_link()
            if flag == True:
                p_vdo.close_form()
                p_adhere.check_video_link_checkbox()
                p_adhere.open_video_form()
                p_vdo.verify_patient_video_page()
            else:
                print("video is linked already")
            now, formatted_now, review_text = p_vdo.fill_up_review_form_ff_off(
                d['drug_name'], d['total_pills'], d['dose_per_pill']
                )

            p_adhere.verify_patient_adherence_page()
            p_adhere.verify_patient_adherence_dose_status("Taken", True)
            p_adhere.verify_patient_adherence_dose_saved_status("Taken", True)
            p_adhere.check_calendar_and_comment_for_adherence(now, formatted_now, review_text)
            return formatted_now, review_text

        home.validate_dashboard_page()
        with checklist_step("dose_submitted_pda_off"), checklist_step("auto_complete_self_report"):
            home.check_for_quick_actions()
            home.check_for_video_review(d["patient_fname"]+" "+d["patient_lname"], d['SA_ID'])
            formatted_now, review_text = _review_video_and_verify_adherence()

        home.click_admin_profile_button()
        profile.logout_user()
        login.after_logout()

        self.__class__.data.update(
            {"commented_timestamp": formatted_now, "commented_text": review_text,
             }
            )