import time

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string, fetch_random_digit
from user_inputs.user_data import UserData


class UserPatientPage(BasePage):
    first_name_text = "pat_fn_" + fetch_random_string()
    last_name_text = "pat_ln_" + fetch_random_string()
    email = "pat_"+fetch_random_string() + "@testmail.com"
    mrn = "mrn_"+fetch_random_digit()
    username = "user_"+fetch_random_string()

    first_name_mob = "pat_fmob_" + fetch_random_string()
    last_name_mob = "pat_lmob_" + fetch_random_string()
    email_mob = "pat_mob_"+fetch_random_string() + "@testmail.com"
    mrn_mob = "mob_"+fetch_random_digit()
    username_mob = "usermob_"+fetch_random_string()

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)


    def fill_patient_form(self, site, mob='NO', rerun_count=0):
        self.wait_for_page_to_load()
        self.wait_for_element('first_name')
        self.wait_for_element('button_SAVE')
        if rerun_count == 0:
            suffix = ""
        else:
            suffix = "1"
        if mob == 'YES':
            self.type('first_name', self.first_name_mob+suffix)
            self.type('last_name', self.last_name_mob+suffix)
            self.type('mrn', self.mrn_mob+suffix)
            self.type('email', suffix+self.email_mob)
            self.type('phone_number', UserData.phone_number)
            self.type('user_name', self.username_mob+suffix)
        else:
            self.type('first_name', self.first_name_text+suffix)
            self.type('last_name', self.last_name_text+suffix)
            self.type('mrn', self.mrn+suffix)
            self.type('email', suffix+self.email)
            self.type('phone_number', UserData.phone_number)
            self.type('user_name', self.username+suffix)

        site_text = self.kendo_dd_get_selected_text('kendo-dropdownlist-site')
        print(site_text, site)
        phn_country_text = self.kendo_dd_get_selected_text('kendo-dropdownlist-phone-country')
        print(site_text, phn_country_text)

        assert site_text == site


        self.click('button_SAVE')
        self.wait_for_invisible('button_SAVE')

        print(f"Patient Created: {self.first_name_text+suffix}, {self.last_name_text+suffix}, {self.mrn+suffix},{suffix+self.email}, {self.username+suffix}, {UserData.phone_number}, {phn_country_text}")
        return self.first_name_text+suffix, self.last_name_text+suffix, self.mrn+suffix, suffix+self.email, self.username+suffix, UserData.phone_number, phn_country_text



