import re
import time

from common_utilities.base_page import BasePage

class ReportsPage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def verify_reports_page(self):
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element('span_Reports')
        name = self.get_text('span_Reports')
        assert name == "Reports", "Reports menu is not opened"
        print("Reports menu is opened")
        assert self.is_element_present('header_Name')
        assert self.is_element_present('header_Description')

    def validate_report_links(self, list_report):
        values = self.get_elements_texts('a_links')
        cleaned = [re.sub(r'^\d+\.\s*', '', item).strip() for item in values if item]

        missing = [x for x in list_report if x not in cleaned]
        assert not missing, f"Missing links: {missing}\nActual: {cleaned}"
