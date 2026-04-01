import time

from common_utilities.base_page import BasePage
from user_inputs.user_data import UserData


class HomePage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def validate_dashboard_page(self, timeout=150):
        self.wait_for_page_to_load(timeout)
        self.verify_page_title("SureAdhere", 60)
        self.wait_for_element("p_Dashboard", 100, strict=True)
        assert self.is_element_visible("p_Dashboard", strict=True), "Its is not the Dashboard"
        print("This is the Dashboard")
        time.sleep(3)

    def validate_not_dashboard_page(self):
        self.wait_for_page_to_load()
        assert not self.is_element_present("p_Dashboard", strict=True)
        time.sleep(3)

    def click_add_user(self):
        self.scroll_to_element("button_add_user")
        self.click("button_add_user")

    def open_manage_staff_page(self):
        self.click('p_Staff', strict=True)
        self.wait_for_page_to_load()
        time.sleep(6)

    def open_dashboard_page(self):
        self.click('p_Dashboard', strict=True)
        self.wait_for_page_to_load(60)
        time.sleep(10)

    def open_reports_page(self):
        self.click('p_Reports', strict=True)
        self.wait_for_page_to_load()
        time.sleep(6)

    def click_admin_profile_button(self):
        time.sleep(2)
        self.wait_for_element("button_user_profile")
        self.click("button_user_profile")

    def verify_presence_of_staff_menu(self, presence=True):
        if presence:
            assert self.is_element_visible('p_Staff', strict=True), "Staff Menu access is missing"
            print("Staff Menu is accessible")
        else:
            assert not self.is_element_visible('p_Staff', strict=True), "Staff Menu is accessible"
            print("Staff Menu is not accessible")

    def verify_presence_of_patient_menu(self, presence=True):
        if presence:
            assert self.is_element_visible('p_Patients', strict=True), "Patient Menu access is missing"
            print("Patient Menu is accessible")
        else:
            assert not self.is_element_visible('p_Patients', strict=True), "Patient Menu is accessible"
            print("Patient Menu is not accessible")

    def verify_presence_of_admin_menu(self, presence=True):
        if presence:
            assert self.is_element_visible('p_Admin', strict=True), "Admin Menu access is missing"
            print("Admin Menu is accessible")
        else:
            assert not self.is_element_visible('p_Admin', strict=True), "Admin Menu is accessible"
            print("Admin Menu is not accessible")

    def verify_presence_of_dashboard_menu(self, presence=True):
        if presence:
            assert self.is_element_visible('p_Dashboard', strict=True), "Dashboard Menu access is missing"
            print("Dashboard Menu is accessible")
        else:
            assert not self.is_element_present('p_Dashboard', strict=True), "Dashboard Menu is accessible"
            print("Dashboard Menu is not accessible")

    def verify_presence_of_reports_menu(self, presence=True):
        if presence:
            assert self.is_element_visible('p_Reports', strict=True), "Reports Menu access is missing"
            print("Reports Menu is accessible")
        else:
            assert not self.is_element_visible('p_Reports', strict=True), "Reports Menu is accessible"
            print("Reports Menu is not accessible")

    def open_manage_patient_page(self):
        self.click('p_Patients', strict=True)
        self.wait_for_page_to_load()
        time.sleep(6)

    def open_admin_page(self):
        self.click('p_Admin', strict=True)
        time.sleep(10)
        self.wait_for_page_to_load(60)

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
        self.js_click("filter_icon")
        time.sleep(2)
        self.wait_for_element("span_Sites", strict=True)
        assert self.is_element_present("div_hide_filter"), "Dashboard Filter is not open"
        print("Dashboard Filter is opened")

    def close_filter(self):
        self.wait_for_element("div_hide_filter")
        self.js_click("div_hide_filter")
        time.sleep(2)
        self.wait_for_invisible("div_hide_filter")
        assert not self.is_element_visible("div_hide_filter"), "Dashboard Filter is not closed"
        print("Dashboard Filter is closed")

    def open_filter_search_staff(self, filter_name,  select=False, name=None,):
        if filter_name!='Sites':
            self.click(f"span_{filter_name}")
        else:
            try:
                self.wait_for_element(f"{filter_name}_bar", 60)
            except:
                self.click(f"span_{filter_name}")
        time.sleep(10)
        self.wait_for_page_to_load(80)
        self.wait_for_element(f"{filter_name}_bar", 60)
        if name and select:
            # values = self.get_li_items(f"{filter_name}_bar")
            # assert name in values, f"{name} not in {filter_name} list"
            self.wait_for_element_rendered(f"global_filter_item_{filter_name}", timeout=80, text=name)
            self.scroll_to_element_rendered(f"global_filter_item_{filter_name}", timeout=80, text=name)
            self.click_rendered(f"global_filter_item_{filter_name}", text=name)
            print(f"{name} present in {filter_name} list")
        elif name is None and select is True:
            self.wait_for_element(f"global_filter_item_{filter_name}_first", strict=True)
            self.scroll_to_element(f"global_filter_item_{filter_name}_first", strict=True)
            self.click(f"global_filter_item_{filter_name}_first", strict=True)
        else:
            print("incorrect parameters")
        self.scroll_to_element(f"span_{filter_name}")
        time.sleep(2)
        self.js_click(f"span_{filter_name}")
        time.sleep(5)
        self.wait_for_page_to_load(80)

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

    def clear_filter(self):
        try:
            self.wait_for_element('reset_filters', strict=True)
            time.sleep(1)
            self.click('reset_filters', strict=True)
            self.wait_for_invisible('reset_filters', strict=True)
        except:
            print("No Filters set")
        time.sleep(1)
        self.wait_for_page_to_load(80)

    def verify_dashboard_elements(self):
        assert self.is_element_present('div-quick_actions'), "Quick Actions not present"
        print("Quick Actions present")
        assert self.is_element_present('div_Adherence'), "Adherence section not present"
        print("Adherence section present")
        assert self.is_element_present('k-tabstrip-tab-New patient videos'), "New patient videos table not present"
        print("New patient videos table present")

    def get_total_pages(self):
        self.wait_for_element('tbody_dashboard')
        text = self.get_text('kendo-pager-info')
        text_list = text.split('of')
        print(text_list[-1].strip())
        return text_list[-1].strip()

    def check_for_quick_actions_elements(self, element, select=True):
        name = None
        if 'missed' in element.lower():
            self.wait_for_element('additional_missed_videos', strict=True)
            self.click('additional_missed_videos', strict=True)
            time.sleep(5)
            name='span-message-patient'
        elif "new" in element.lower():
            self.wait_for_element('additional_videos', strict=True)
            self.click('additional_videos', strict=True)
            time.sleep(5)
            self.unheal('span-patient-video-review')
            self.unheal_all('span-patient-video-review')
            name='span-patient-video-review'
        elif "low" in element.lower():
            self.wait_for_element('additional_low_review_rate', strict=True)
            self.click('additional_low_review_rate', strict=True)
            time.sleep(5)
            name = 'span-email-staff'
        else:
            print("Unknown value")
        list_review = self.find_elements(name)
        print(f"for {element} section {len(list_review)} patient present")
        if len(list_review) != 0:
            if select:
                self.click(logical_name=name)
                time.sleep(10)
                self.wait_for_page_to_load(80)
            else:
                self.is_element_present_rendered(logical_name=name, index=1)
        else:
            print("No element present")
    def verify_dashboard_table_data(self, presence=True, patient_manager=None, treatment_monitor=None, video=None):
        self.wait_for_page_to_load(60)
        self.scroll_to_element('k-tabstrip-tab-New patient videos')
        if presence:
            assert self.is_element_present('table_no_data', strict=True) == False, "No data is present"
            print("Data is present")
        else:
            assert self.is_element_present('table_no_data', strict=True) == True, "Data is still present"
            print("No data is present")

        if patient_manager:
            pm_list_data = self.find_elements('td_patient_manager')
            print(len(pm_list_data))
            for item in pm_list_data:
                assert patient_manager in item.text, f"{patient_manager} doesnot match {item.text}"
                print(f"{patient_manager} matches {item.text}")

        if treatment_monitor:
            tm_list_data = self.find_elements('td_treatment_monitor')
            print(len(tm_list_data))
            for item in tm_list_data:
                assert treatment_monitor in item.text, f"{treatment_monitor} doesnot match {item.text}"
                print(f"{treatment_monitor} matches {item.text}")

        if video:
            vdo_list_data = self.find_elements('td_recorded')
            print(len(vdo_list_data))
            for item in vdo_list_data:
                assert item.text is not None, f"Value not present"
                print(f"{item.text} present for this row")

    def check_for_adherence_section(self):
        self.scroll_to_element('div_Adherence')
        time.sleep(2)
        print("Adherence is present")
        assert self.is_element_present('kendo-dropdownlist_adherence')
        assert self.is_element_present('moveChartLeft')
        assert self.is_element_present('moveChartRight')
        assert self.is_element_present('areaChart')
        assert self.is_element_present('columnChart')
        print("All Adherence section elements are present")

    def validate_graph_for_selection(self, selection):
        self.scroll_to_element('div_Adherence')
        time.sleep(3)
        self.wait_for_element('kendo-dropdownlist_adherence')
        self.kendo_dd_select_text_old('kendo-dropdownlist_adherence', selection)
        text=self.kendo_dd_get_selected_text('kendo-dropdownlist_adherence')
        print(f"selected value is {text}")
        data_list = self.get_bar_breakdown()
        print(data_list)
        text_dose = self.get_text('div_for_doses')
        assert selection.lower() in text_dose and data_list is not None, f"{selection.lower} not present in {text_dose}"
        print(f"{selection.lower} present in {text_dose}")
        time.sleep(5)
        if '7' in selection:
            self.validate_kendo_bar_chart(7)
        elif '30' in selection:
            self.validate_kendo_bar_chart(30)

    def verify_prev_next_buttons(self, prev=False, next=False):
        self.scroll_to_element('div_Adherence')
        self.kendo_dd_select_text_old('kendo-dropdownlist_adherence', UserData.adherence_dropdown[0])
        text = self.kendo_dd_get_selected_text('kendo-dropdownlist_adherence')
        print(text)
        get_default_list = self.get_current_labels()
        print("Default labels:", get_default_list)
        default_dates = self.parse_labels_to_dates(get_default_list)
        print("Default dates:", default_dates)
        if prev:
            self.click('moveChartLeft')
        elif next:
            self.click('moveChartRight')
        time.sleep(10)
        self.wait_for_page_to_load()
        get_new_labels = self.get_current_labels()
        print("New labels:", get_new_labels)
        new_dates = self.parse_labels_to_dates(get_new_labels)
        print("New dates:", new_dates)
        assert default_dates and new_dates, "Could not parse dates from chart labels"
        if prev:
            assert min(new_dates) < min(default_dates), \
                f"❌ Prev button did not shift to past dates. New min: {min(new_dates)}, Default min: {min(default_dates)}"
            print(f"✅ Prev button validated: new dates ({min(new_dates)}) are before default ({min(default_dates)})")
        elif next:
            assert min(new_dates) > min(default_dates), \
                f"❌ Next button did not shift to future dates. New min: {min(new_dates)}, Default min: {min(default_dates)}"
            print(f"✅ Next button validated: new dates ({min(new_dates)}) are after default ({min(default_dates)})")


    def change_to_area_graph(self, flag=True):
        time.sleep(5)
        text = self.get_attribute('areaChart', 'class')
        print(text)
        if flag:
            if 'disabled' in text:
                print("Area graph is enabled")
            else:
                self.click('areaChart')
                time.sleep(5)
                text = self.get_attribute('areaChart', 'class')
                print(text)
                assert 'disabled' in text, "Graph is still disabled"
                print('Area graph is enabled')
        elif flag ==False:
            if 'disabled' not in text:
                print("Area graph is not enabled")
            else:
                self.click('areaChart')
                time.sleep(5)
                text = self.get_attribute('areaChart', 'class')
                print(text)
                assert 'disabled' not in text, "Graph is still enabled"
                print('Area graph is disabled')
        else:
            print("Invalid paramenter")

    def change_to_bar_graph(self, flag=True):
        time.sleep(5)
        text = self.get_attribute('columnChart', 'class')
        print(text)
        if flag:
            if 'disabled' in text:
                print("Bar graph is enabled")
            else:
                self.click('columnChart')
                time.sleep(5)
                text = self.get_attribute('columnChart', 'class')
                print(text)
                assert 'disabled' in text, "Graph is still disabled"
                print('Bar graph is enabled')
        elif flag ==False:
            if 'disabled' not in text:
                print("Bar graph is not enabled")
            else:
                self.click('columnChart')
                time.sleep(5)
                text = self.get_attribute('columnChart', 'class')
                print(text)
                assert 'disabled' not in text, "Graph is still enabled"
                print('Bar graph is disabled')
        else:
            print("Invalid paramenter")

    def adherence_area_graph_hover(self, selection):
        self.scroll_to_element('div_Adherence')
        time.sleep(3)
        self.wait_for_element('kendo-dropdownlist_adherence')
        self.kendo_dd_select_text_old('kendo-dropdownlist_adherence', selection)
        text = self.kendo_dd_get_selected_text('kendo-dropdownlist_adherence')
        time.sleep(20)
        self.wait_for_page_to_load(60)
        print(f"selected value is {text}")
        values=self.kendo_area_graph_hover()
        print(values)