import time

from common_utilities.base_page import BasePage

class HomePage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def validate_dashboard_page(self):
        self.wait_for_page_to_load(150)
        self.verify_page_title("SureAdhere", 60)
        self.wait_for_element("p_Dashboard", 100)
        assert self.is_element_visible("p_Dashboard"), "Its is not the Dashboard"
        print("This is the Dashboard")
        time.sleep(3)

    def validate_not_dashboard_page(self):
        self.wait_for_page_to_load()
        assert not self.is_element_present("p_Dashboard")
        time.sleep(3)

    def click_add_user(self):
        self.click("button_add_user")

    def open_manage_staff_page(self):
        self.click('p_Staff')
        self.wait_for_page_to_load()
        time.sleep(6)

    def open_dashboard_page(self):
        self.click('p_Dashboard')
        self.wait_for_page_to_load(150)
        time.sleep(6)

    def open_reports_page(self):
        self.click('p_Reports')
        self.wait_for_page_to_load()
        time.sleep(6)

    def click_admin_profile_button(self):
        time.sleep(2)
        self.wait_for_element("button_user_profile")
        self.click("button_user_profile")

    def verify_presence_of_staff_menu(self, presence=True):
        if presence:
            assert self.is_element_visible('p_Staff'), "Staff Menu access is missing"
            print("Staff Menu is accessible")
        else:
            assert not self.is_element_visible('p_Staff'), "Staff Menu is accessible"
            print("Staff Menu is not accessible")

    def verify_presence_of_patient_menu(self, presence=True):
        if presence:
            assert self.is_element_visible('p_Patients'), "Patient Menu access is missing"
            print("Patient Menu is accessible")
        else:
            assert not self.is_element_visible('p_Patients'), "Patient Menu is accessible"
            print("Patient Menu is not accessible")

    def verify_presence_of_admin_menu(self, presence=True):
        if presence:
            assert self.is_element_visible('p_Admin'), "Admin Menu access is missing"
            print("Admin Menu is accessible")
        else:
            assert not self.is_element_visible('p_Admin'), "Admin Menu is accessible"
            print("Admin Menu is not accessible")

    def verify_presence_of_dashboard_menu(self, presence=True):
        if presence:
            assert self.is_element_visible('p_Dashboard'), "Dashboard Menu access is missing"
            print("Dashboard Menu is accessible")
        else:
            assert not self.is_element_present('p_Dashboard'), "Dashboard Menu is accessible"
            print("Dashboard Menu is not accessible")

    def verify_presence_of_reports_menu(self, presence=True):
        if presence:
            assert self.is_element_visible('p_Reports'), "Reports Menu access is missing"
            print("Reports Menu is accessible")
        else:
            assert not self.is_element_visible('p_Reports'), "Reports Menu is accessible"
            print("Reports Menu is not accessible")

    def open_manage_patient_page(self):
        self.click('p_Patients')
        self.wait_for_page_to_load()
        time.sleep(6)

    def open_admin_page(self):
        self.click('p_Admin')
        time.sleep(6)
        self.wait_for_page_to_load()

    def check_for_quick_actions(self):
        self.wait_for_element('div-quick_actions')
        time.sleep(5)
        print("Quick Actions is present")

    def check_for_video_review(self, pat_name, sa_id):
        self.unheal('span-patient-video-review')
        self.unheal_all('span-patient-video-review')
        self.wait_for_element('additional_videos', strict=True)
        self.click('additional_videos', strict=True)
        time.sleep(5)
        list_name = self.find_elements('span-video-patient_name')
        list_review = self.find_elements('span-patient-video-review')
        list_sa_id = self.find_elements('span-patient-sa-id-review')
        print(len(list_name), len(list_review), len(list_sa_id))
        for vids, sa_id_value in zip(list_review, list_sa_id):
            sa_id_text = sa_id_value.text.strip()
            if sa_id in sa_id_text:
                print(f"{sa_id} is present. Matches {sa_id_text}")
                vids.click()
                time.sleep(6)
                self.wait_for_page_to_load(80)
                break  # stop looping after success
            else:
                print(f"{sa_id} does not match {sa_id_text}")
        else:
            # Only runs if the loop completes without 'break'
            print(f"No matching SA ID found for {sa_id}")

    def verify_announcement(self, announcement_text, flag=True):
        self.wait_for_element('div_alert', 100)
        alert_text = self.get_text('div_alert')
        print(alert_text)
        assert alert_text.strip() == announcement_text, f"{announcement_text} not present"
        print(f"{announcement_text} is present")

    def stay_idle(self, timeout, active=True):
        self.open_dashboard_page()
        print(f"Starting {timeout} minutes of inactivity")
        # self.idle_wait(timeout*60)
        time.sleep(timeout*60)
        if active==True:
            self.open_admin_page()
            self.open_dashboard_page()
            self.refresh()
            self.validate_dashboard_page()
            assert True, "Session not active"
            print(f"Session active even after {timeout} minutes of inactivity.")
        else:
            self.refresh()
            self.wait_for_page_to_load(150)
            time.sleep(20)
            self.validate_not_dashboard_page()
            assert True, "Session is still active"
            print(f"Session inactive after {timeout} minutes of inactivity.")

    def open_filter(self):
        self.wait_for_element("filter_icon")
        self.click("filter_icon")
        self.wait_for_element("span_Site", strict=True)
        assert self.is_element_present("div_hide_filter"), "Dashboard Filter is not open"
        print("Dashboard Filter is opened")

    def close_filter(self):
        self.wait_for_element("div_hide_filter")
        self.click("div_hide_filter")
        self.wait_for_invisible("div_hide_filter")
        assert not self.is_element_visible("div_hide_filter"), "Dashboard Filter is not closed"
        print("Dashboard Filter is closed")

    def open_filter_search_staff(self, filter_name, name):
        self.click(f"span_{filter_name}")
        time.sleep(5)
        self.wait_for_page_to_load(80)
        time.sleep(6)
        self.wait_for_element(f"{filter_name}_bar", 60)
        values = self.get_li_items(f"{filter_name}_bar")
        # print(values)
        assert name in values, f"{name} not in list"
        print(f"{name} present in list")
        self.click(f"span_{filter_name}")

    def verify_filter_presence(self, filter_name, presence=True):
        strict = True
        if presence:
            assert self.is_element_visible(f"span_{filter_name}", strict=strict), f"{filter_name} is not present"
            print(f"{filter_name} is present")
        else:
            assert not self.is_element_visible(f"span_{filter_name}", strict=strict), f"{filter_name} is present"
            print(f"{filter_name} is not present")


    def verify_data_table_presence(self, presence=True):
        if presence:
            assert self.is_element_visible("dashboard_data_table"), "Patient Data Table is not present"
            print("Patient Data Table is present")
        else:
            assert not self.is_element_visible("dashboard_data_table"), "Patient Data Table is present"
            print("Patient Data Table is not present")

    def verify_div_chart_presence(self, presence=True):
        if presence:
            assert self.is_element_visible("div_chart"), "Data Chart is not present"
            print("Data Chart is present")
        else:
            assert not self.is_element_visible("div_chart"), "Data Chart is present"
            print("Data Chart is not present")

