import time
import re
from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string, fetch_random_digit
from user_inputs.user_data import UserData


class PatientProfilePage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def verify_patient_profile_page(self):
        time.sleep(5)
        self.wait_for_page_to_load()
        self.wait_for_element('k-opened-tabstrip-tab', 50)
        self.wait_for_element("input_First_name", 100)
        tabname = self.get_text('k-opened-tabstrip-tab')
        assert tabname == "Profile", "Profile tab is not opened"
        print("Opened tab is Profile")

    def verify_patient_profile_details(self, fname, lname, mrn, email, user_name, phn, phn_country, site, active_account=None, sa_id=False):
        self.wait_for_field_value_contains('input_First_name', fname)
        fn_value = self.get_value("input_First_name")
        ln_value = self.get_value("input_Last_name")
        mrn_value = self.get_value("input-mrn")
        email_value = self.get_value("email")
        username_value = self.get_value("user_name")
        phn_value = self.get_value("phone_number")
        fullname_text = self.get_text("div_patient_name")
        print(fullname_text)
        fullname_text = fullname_text.split("|")

        assert str(fullname_text[0]).strip() == fname + " " + lname

        phn_country_text = self.kendo_dd_get_selected_text('kendo-dropdownlist-phone-country')
        print(str(fullname_text[0]).strip(), str(fullname_text[1]).strip(), phn_country_text)

        assert phn_country_text == phn_country
        assert str(fullname_text[1]).strip() == site
        assert fn_value == fname
        assert ln_value == lname
        assert mrn_value == mrn
        assert email_value == email
        assert username_value == user_name
        # assert phn_value == phn
        assert re.sub(r"\D+", "", phn_value) == re.sub(r"\D+", "", phn), "Phone mismatch"

        if active_account == False:
            assert not self.is_checked('accountIsActiv_chb'), "Account is active"
            print("Account is inactive correctly")
        elif active_account == True:
            assert self.is_checked('accountIsActiv_chb'), "Account is inactive"
            print("Account is active correctly")
        else:
            print("Account active check is not requested")

        print("All basic values matched")
        if sa_id:
            sa_id = self.get_text("label_SA_ID_value")
            return sa_id
        else:
            return None


    def wait_for_patient_to_load(self, fname, lname):
        self.wait_for_field_value_contains('input_First_name', fname)
        self.wait_for_field_value_contains('input_Last_name', lname)

    def edit_patient_form(self,mfname, mlname,  fname, lname, mrn, email, username, phn, country, site, sa_id):
        manager_fullname = mfname + " " + mlname
        print(manager_fullname)
        self.wait_for_patient_to_load(fname, lname)
        self.verify_patient_profile_details(fname, lname, mrn, email, username, phn, country, site)
        self.kendo_dd_select_text_old("kendo-dropdownlist-patient-manager", manager_fullname, match="exact", timeout=25)
        self.inactive_patient()

        account_active = False
        new_fname=fname+"_new"
        new_lname=lname+"_new"
        self.type('input_First_name', new_fname)
        self.type('input_Last_name', new_lname)


        self.click_robust('button_SAVE')
        # self.wait_for_invisible('button_SAVE')
        time.sleep(1)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            assert "Profile saved" in self.kendo_dialog_get_text()
            self.kendo_dialog_click_button("Ok")
        except Exception:
            print("popup not present after save")

        print(new_fname, new_lname)
        print(self.resolve("kendo-dropdownlist-patient-manager"))
        patient_manager = self.kendo_dd_get_selected_text(logical_name="kendo-dropdownlist-patient-manager")
        print(f"Selected manager is {patient_manager}")
        assert patient_manager.strip() == manager_fullname

        return new_fname, new_lname, account_active

    def select_patient_manager(self, manager_fullname):
        self.kendo_dd_select_text_old("kendo-dropdownlist-patient-manager", manager_fullname, match="exact", timeout=25)
        print(self.resolve("kendo-dropdownlist-patient-manager"))
        patient_manager = self.kendo_dd_get_selected_text(logical_name="kendo-dropdownlist-patient-manager")
        print(f"Selected manager is {patient_manager}")
        assert patient_manager.strip() == manager_fullname
        self.click_robust('button_SAVE')
        # self.wait_for_invisible('button_SAVE')
        time.sleep(1)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            assert "Profile saved" in self.kendo_dialog_get_text()
            self.kendo_dialog_click_button("Ok")
        except Exception:
            print("popup not present after save")

    def active_patient(self):
        print(self.resolve("accountIsActiv_chb"))
        if self.is_checked('accountIsActiv_chb'):
            print("Account is already set to active")
        else:
            print("Account is active is not selected")
            self.click("accountIsActiv_chb")
            assert self.is_checked('accountIsActiv_chb')
            print("Account is not set to active")


    def inactive_patient(self):
        if self.is_checked('accountIsActiv_chb'):
            print("Account is active is selected")
            self.click("accountIsActiv_chb")
            assert not self.is_checked('accountIsActiv_chb')
            print("Account is set to inactive")
        else:
            print("Account is already set to inactive")

    def set_patient_pin(self,fname, lname, mrn, email, username, phn, country, site):
        self.wait_for_patient_to_load(fname, lname)
        self.verify_patient_profile_details(fname, lname, mrn, email, username, phn, country, site)

        self.active_patient()
        account_active = True

        self.click_robust('button_SAVE')
        # self.wait_for_invisible('button_SAVE')
        time.sleep(1)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            assert "Profile saved" in self.kendo_dialog_get_text()
            self.kendo_dialog_click_button("Ok")
            self.wait_for_overlays_to_clear(5)
        except Exception:
            print("popup not present after save")

        self.click_robust('button_SEND/RESET')

        self.kendo_dialog_wait_open()
        text = self.kendo_dialog_get_text()
        print(text)

        pin = text.split(":")
        pin = pin[1].strip()
        print(pin)
        self.kendo_dialog_click_button("Ok")
        self.kendo_dialog_wait_close()
        self.wait_for_overlays_to_clear(5)

        return account_active, pin
