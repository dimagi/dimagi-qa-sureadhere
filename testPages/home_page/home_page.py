import time

from common_utilities.base_page import BasePage

class HomePage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def validate_dashboard_page(self):
        self.wait_for_page_to_load()
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

    def open_dashboard_page(self):
        self.click('p_Dashboard')
        self.wait_for_page_to_load()

    def click_admin_profile_button(self):
        time.sleep(2)
        self.wait_for_element("button_user_profile")
        self.click("button_user_profile")

    def open_manage_patient_page(self):
        self.click('p_Patients')
        self.wait_for_page_to_load()

    def open_admin_page(self):
        self.click('p_Admin')
        time.sleep(5)
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
                time.sleep(10)
                self.wait_for_page_to_load()
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
