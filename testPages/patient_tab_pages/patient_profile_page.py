import time
import re
from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string, fetch_random_digit
from user_inputs.user_data import UserData


class PatientProfilePage(BasePage):

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def verify_patient_profile_page(self):
        time.sleep(15)
        self.wait_for_page_to_load()
        self.wait_for_element('k-opened-tabstrip-tab', 50)
        self.wait_for_element("input_First_name", 100)
        self.unheal_all('k-opened-tabstrip-tab')
        time.sleep(3)
        tabname = self.get_text('k-opened-tabstrip-tab')
        print(tabname)
        assert tabname == "Profile", "Profile tab is not opened"
        print("Opened tab is Profile")

    def verify_patient_profile_details(self, fname, lname, mrn, email, user_name, phn, phn_country, site, active_account=None, sa_id=False, account_test=None):
        self.wait_for_field_value_contains('input_First_name', fname)
        fn_value = self.get_value("input_First_name")
        ln_value = self.get_value("input_Last_name")
        mrn_value = self.get_value("input-mrn")
        email_value = self.get_value("email")
        username_value = self.get_value("user_name")
        phn_value = self.get_value("phone_number")
        fullname_text = self.get_full_text("div_patient_name", strict=True)
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

        if account_test == False:
            assert not self.is_checked('accountIsTest_chb'), "Account is test"
            print("Account is not test")
        elif account_test == True:
            assert self.is_checked('accountIsTest_chb'), "Account is not test"
            print("Account is test")
        else:
            print("Account Test check is not requested")

        print("All basic values matched")
        if sa_id:
            sa_id = self.get_text("label_SA_ID_value")
            return sa_id
        else:
            return None


    def wait_for_patient_to_load(self, fname, lname):
        self.wait_for_field_value_contains('input_First_name', fname)
        self.wait_for_field_value_contains('input_Last_name', lname)

    def edit_patient_form(self,mfname, mlname,  fname, lname, mrn, email, username, phn, country, site, sa_id, patient_manager=True, treatment_monitor=True, active_patient=False):
        manager_fullname = mfname + " " + mlname
        print(manager_fullname)
        self.wait_for_patient_to_load(fname, lname)
        self.verify_patient_profile_details(fname, lname, mrn, email, username, phn, country, site)
        if patient_manager:
            self.kendo_dd_select_text_old("kendo-dropdownlist-patient-manager", manager_fullname, match="exact", timeout=25)
        if treatment_monitor:
            self.kendo_dd_select_text_old("kendo-dropdownlist-treatment-monitor", manager_fullname, match="exact",
                                          timeout=25
                                          )
        if active_patient:
            self.active_patient()
            account_active = True
        else:
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

        if patient_manager:
            patient_manager_name = self.kendo_dd_get_selected_text(logical_name="kendo-dropdownlist-patient-manager")
            print(f"Selected manager is {patient_manager_name}")
            assert patient_manager_name.strip() == manager_fullname
        if treatment_monitor:
            treatment_monitor_name = self.kendo_dd_get_selected_text(logical_name="kendo-dropdownlist-treatment-monitor")
            print(f"Selected Monitor is {treatment_monitor_name}")
            assert treatment_monitor_name.strip() == manager_fullname

        return new_fname, new_lname, account_active

    def save_patient_changes(self):
        self.click_robust('button_SAVE')
        # self.wait_for_invisible('button_SAVE')
        time.sleep(1)
        try:
            self.kendo_dialog_wait_open()  # no title constraint
            assert "Profile saved" in self.kendo_dialog_get_text()
            self.kendo_dialog_click_button("Ok")
        except Exception:
            print("popup not present after save")

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

    def select_treatment_monitor(self, manager_fullname):
        self.kendo_dd_select_text_old("kendo-dropdownlist-treatment-monitor", manager_fullname, match="exact", timeout=25)
        print(self.resolve("kendo-dropdownlist-treatment-monitor"))
        patient_manager = self.kendo_dd_get_selected_text(logical_name="kendo-dropdownlist-treatment-monitor")
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
        self.wait_for_element("accountIsActiv_chb")
        self.scroll_to_element("accountIsActiv_chb")
        print(self.resolve("accountIsActiv_chb"))
        if self.is_checked('accountIsActiv_chb'):
            print("Account is already set to active")
        else:
            print("Account is active is not selected")
            self.js_click("accountIsActiv_chb")
            assert self.is_checked('accountIsActiv_chb')
            print("Account is set to active")


    def inactive_patient(self):
        self.wait_for_element("accountIsActiv_chb")
        self.scroll_to_element("accountIsActiv_chb")
        if self.is_checked('accountIsActiv_chb'):
            print("Account is active is selected")
            self.js_click("accountIsActiv_chb")
            assert not self.is_checked('accountIsActiv_chb')
            print("Account is set to inactive")
        else:
            print("Account is already set to inactive")

    def test_patient(self, flag):
        if flag == True and self.is_checked('accountIsTest_chb'):
            print("Test account is already checked")
        elif flag == False and not self.is_checked('accountIsTest_chb'):
            print("Test account is already unchecked")
        else:
            self.wait_for_element("accountIsTest_chb")
            self.scroll_to_element("accountIsTest_chb")
            self.js_click("accountIsTest_chb")
            state = self.is_checked('accountIsTest_chb')
            print(f"Test account is set to {state}")

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

    def verify_patient_profile_additional_details(self):
        self.scroll_to_element("kendo-dropdownlist-preferred-language")
        preferred_language = self.kendo_dd_get_selected_text(logical_name="kendo-dropdownlist-preferred-language")
        print(f"Selected Preferred Language is {preferred_language}")
        assert preferred_language.strip() == "English"
        self.scroll_to_element("kendo-switch_Reminder settings", strict=True)
        flag = self.get_attribute("kendo-switch_Reminder settings", "aria-check", strict=True)
        print(f"Reminder settings is set to {flag}")
        assert flag != True
        if self.is_checked('accountIsActiv_chb'):
            return True
        else:
            return False


    def verify_mandatory_fields_with_invalid_data(self, fname, lname, mrn, email, username, phn, country, site, sa_id):
        self.load_patient(fname, lname, mrn, email, username, phn, country, site, sa_id)

        assert self.is_enabled("user_name") == False, "Username field is enabled"
        print("Username field is disabled")
        assert self.is_enabled("input-mrn") == True, "MRN field is not enabled"
        print("Username field is enabled")
        assert self.is_enabled("phone_number") == True, "Username field is not enabled"
        print("Username field is enabled")

        self.clear("input-mrn")
        self.clear("phone_number")

        self.type("email", UserData.invalid_email)
        time.sleep(2)
        self.wait_for_element('missing_mrn')

        assert self.is_element_visible('missing_mrn'), "Error 'Valid MRN/ID required.' is not present"
        print("Error 'Valid MRN/ID required.' is present")
        assert self.is_element_visible('missing_phone_number'), "Error 'Valid phone number is required' is not present"
        print("Error 'Valid phone number is required' is present")
        assert self.is_element_visible('invalid_email'), "Error 'Valid email is required' is not present"
        print("Error 'Valid email is required' is present")

        self.click_robust('button_CANCEL')
        time.sleep(3)
        self.wait_for_page_to_load()
        self.scroll_to_element("input_First_name")
        self.wait_for_field_value_contains('input-mrn', mrn)
        self.wait_for_field_value_contains('email', email)


    def edit_mandatory_fields_with_valid_data(self, fname, lname, mrn, email, username, phn, country, site, sa_id):
        self.wait_for_patient_to_load(fname, lname)
        self.verify_patient_profile_details(fname, lname, mrn, email, username, phn, country, site, sa_id)
        new_fname = fname + "_new"
        new_lname = lname + "_new"
        new_email = f"n{email}"
        self.type('input_First_name', new_fname)
        self.type('input_Last_name', new_lname)
        self.type("email", new_email)

        self.scroll_to_element("kendo-dropdownlist-alt-phone-country")
        self.kendo_dd_select_text_old("kendo-dropdownlist-alt-phone-country", country, match="exact", timeout=25)
        time.sleep(2)
        self.wait_for_element("alt_phone_number")
        self.type("alt_phone_number", phn)

        self.save_patient_changes()
        return new_fname, new_lname, new_email

    def load_patient(self, fname, lname, mrn, email, username, phn, country, site, sa_id):
        self.wait_for_patient_to_load(fname, lname)
        self.verify_patient_profile_details(fname, lname, mrn, email, username, phn, country, site, sa_id)


