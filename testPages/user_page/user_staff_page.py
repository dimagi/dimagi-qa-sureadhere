import time

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string
from user_inputs.user_data import UserData


class UserStaffPage(BasePage):
    # first_name_text = "test_first_" + fetch_random_string()
    # last_name_text = "test_last_" + fetch_random_string()
    # email = fetch_random_string() + "@testmail.com"

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)

    def fill_staff_form(self, site_manager, manager = UserData.default_managers, login=None, test_account=None, incorrect=False, rerun=0):
        first_name_text = f"test_fst_{rerun}{fetch_random_string()}{login}" if login is not None else f"test_first_{fetch_random_string()}"
        last_name_text = f"test_lst_{rerun}{fetch_random_string()}{login}" if login is not None else f"test_last_{fetch_random_string()}"
        email = f"{fetch_random_string()}{rerun}{login}@testmail.com" if login is not None else f"{fetch_random_string()}@testmail.com"

        self.wait_for_element('first_name')
        self.type('first_name', first_name_text)
        self.type('last_name', last_name_text)
        self.type('email', email)
        self.type('password', UserData.pwd)
        self.type('phone_number', UserData.phone_number)

        if 'PM' in manager:
            self.click('selectedPatientManagers')
            self.kendo_select("k-input_Patient_Manager", text=site_manager)

        if 'TM' in manager:
            self.click('selectedTreatmentMonitors')
            self.kendo_select("k-input_Treatment_Monitors", text=site_manager)

        if 'SM' in manager:
            self.click('selectedSiteManagers')
            self.kendo_select("k-input_Site_Managers", text=site_manager)

        if 'SS' in manager:
            self.click('selectedStaffAdministrators')
            self.kendo_select("k-input_Staff_Administrators", text=site_manager)

        if test_account:
            self.click('isTest')
            assert self.is_checked('isTest'), "Test account  is not selected"
            print("Test account is selected")
        else:
            assert not self.is_checked('isTest'), "Test account is selected"
            print("Not Test account")

            self.click('isClientAdmin')
            assert self.is_checked('isClientAdmin'), "Client Admin not checked"

            self.click('isRegimenEditor')
            assert self.is_checked('isRegimenEditor'), "Regimen Editor not checked"

        if incorrect:
            if incorrect == 'password':
                self.edit_staff_form_with_incorrect_data(first_name_text, last_name_text, password_test=True)
            elif incorrect == 'email':
                self.edit_staff_form_with_incorrect_data(first_name_text, last_name_text, email_test=True)
            return None
        else:
            self.click('button_SUBMIT')
            self.wait_for_invisible('button_SUBMIT')
            client=True
            self.wait_for_page_to_load(50)
            time.sleep(10)
            print(f"Staff Created: {first_name_text}, {last_name_text}, {email}, {UserData.phone_number}")
            return first_name_text, last_name_text, email, UserData.phone_number, client, site_manager

    def wait_for_staff_to_load(self, fname, lname):
        self.wait_for_field_value_contains('first_name', fname, timeout=40)
        self.wait_for_field_value_contains('last_name', lname, timeout=40)

    def edit_staff_form(self, fname, lname, email, phn, client):
        self.wait_for_staff_to_load(fname, lname)
        self.verify_basic_staff_data(fname, lname, email, phn, client=client)
        # assert self.is_checked('isClientAdmin'), "Client Admin not check"
        # print("Client Admin is selected")

        if self.is_checked('isActive'):
            account_active = True
            print("Account is active is selected")
        else:
            account_active = False
            print("Account is active is not selected")

        new_fname=fname+"_new"
        new_lname=lname+"_new"
        self.type('first_name', new_fname)
        self.type('last_name', new_lname)

        self.click('isTest')
        print("Test account is selected")
        if self.is_checked('isTest'):
            test_account=True
            print("Test account  is selected")
        else:
            test_account = False
            print("Test account  is not selected")


        self.click('button_SUBMIT')
        self.wait_for_invisible('button_SUBMIT')
        print(new_fname, new_lname, account_active, test_account)
        return new_fname, new_lname, account_active, test_account


    def make_staff_active(self, fname, lname, email, phn):
        self.wait_for_staff_to_load(fname, lname)
        self.verify_basic_staff_data(fname, lname, email, phn)

        if self.is_checked('isActive'):
            print("Account is already active")
        else:
            self.click('isActive')
            assert self.is_checked('isActive')
            print("Account is active is now selected")

        if not self.is_checked('isTest'):
            print("Account is not Test")
        else:
            self.click('isTest')
            assert not self.is_checked('isTest')
            print("Account is Test is now unselected")

        self.click('button_SUBMIT')
        self.wait_for_invisible('button_SUBMIT')


    def verify_basic_staff_data(self, fname, lname, email, phn, client=None, active=None, test=None):
        fn_value = self.get_value("first_name")
        ln_value = self.get_value("last_name")
        email_value = self.get_value("email")
        phn_value = self.get_value("phone_number")
        assert fn_value == fname
        assert ln_value == lname
        assert email_value == email
        assert phn_value == phn
        print("All basic values matched")
        if client==True:
            assert self.is_checked('isClientAdmin'), "Client Admin is not selected"
            print("Client Admin is selected")
        if active==True:
            assert self.is_checked('isActive'), "Account is active is not selected"
            print("Account is active is selected")
        if test==True:
            assert self.is_checked('isTest'), "Test account  is not selected"
            print("Test account is selected")

    def validate_blank_form_submission(self):
        self.wait_for_element('first_name')
        print(self.resolve('button_CLOSE'))
        print(self.resolve('button_SUBMIT'))
        self.click('button_SUBMIT')
        self.wait_for_element('missing_first_name')

        assert self.is_element_visible('missing_first_name'), "Error 'Valid first name is required' is not present"
        print("Error 'Valid first name is required' is present")
        assert self.is_element_visible('missing_last_name'), "Error 'Valid last name is required' is not present"
        print("Error 'Valid last name is required' is present")
        assert self.is_element_visible('missing_email'), "Error 'Valid email is required' is not present"
        print("Error 'Valid email is required' is present")
        assert self.is_element_visible('missing_password'), "Error 'Valid password is required' is not present"
        print("Error 'Valid password is required' is present")
        assert self.is_element_visible('missing_phone_number'), "Error 'Valid phone number is required' is not present"
        print("Error 'Valid phone number is required' is present")
        self.cancel_form()

    def fill_staff_form_without_site_manager(self, login=None):
        first_name_text = f"test_first_{fetch_random_string()}{login}" if login is not None else f"test_first_{fetch_random_string()}"
        last_name_text = f"test_last_{fetch_random_string()}{login}" if login is not None else f"test_last_{fetch_random_string()}"
        email = f"{fetch_random_string()}{login}@testmail.com" if login is not None else f"{fetch_random_string()}@testmail.com"

        self.type('first_name', first_name_text)
        self.type('last_name', last_name_text)
        self.type('email', email)
        self.type('password', UserData.pwd)
        self.type('phone_number', UserData.phone_number)

        self.click('button_SUBMIT')
        self.wait_for_element('missing_site_manager')

        assert self.is_element_visible('missing_site_manager'), "Error 'At least one role must be chosen' is not present"
        print("Error 'At least one role must be chosen' is present")
        self.cancel_form()


    def edit_staff_form_with_incorrect_data(self, fname, lname, password_test=False, email_test=False):
        self.wait_for_staff_to_load(fname, lname)

        if password_test:
            self.type('password', "xxx")
        if email_test:
            self.type('email', UserData.reset_email_address)
        self.click('button_SUBMIT')
        if password_test:
            self.wait_for_element('staff_error_message')
            text = self.get_text('staff_error_message')
            assert UserData.password_error in text.strip(), f"{text} doesn't match {UserData.password_error}"
            print(f"{text} matches {UserData.password_error}")
        if email_test:
            self.kendo_dialog_wait_open()  # no title constraint
            text = self.kendo_dialog_get_text()
            assert UserData.email_error in text.strip(), f"{text} doesn't match {UserData.email_error}"
            print(f"{text} matches {UserData.email_error}")
            self.kendo_dialog_click_button("Ok")
        time.sleep(1)
        self.cancel_form()

    def cancel_form(self):
        time.sleep(2)
        self.kendo_dialog_close()

    def edit_staff_info_options(self, fname, lname, name_change=None, add_pm=None, add_sm=None, add_tm=None, add_ss=None, test_acc=None,
                                active_acc=None, client_acc=None, remove_managers=None, blind_trial=None, global_data=None):
        self.wait_for_staff_to_load(fname, lname)
        if name_change == True:
            new_fname = str(fname).replace("test_f","test_nf")
            new_lname = str(lname).replace("test_l", "test_nl")
            print(new_fname, new_lname)
            self.type('first_name', new_fname)
            self.type('last_name', new_lname)
        else:
            print("No name changes")

        if add_pm != None:
            self.click('selectedPatientManagers')
            self.kendo_select("k-input_Patient_Manager", text=add_pm)

        if add_tm != None:
            self.click('selectedTreatmentMonitors')
            self.kendo_select("k-input_Treatment_Monitors", text=add_tm)

        if add_sm != None:
            self.click('selectedSiteManagers')
            self.kendo_select("k-input_Site_Managers", text=add_sm)

        if add_ss != None:
            self.click('selectedStaffAdministrators')
            self.kendo_select("k-input_Staff_Administrators", text=add_ss)

        if client_acc != None:
            self.set_staff_account_checkbox(setting_name='isClientAdmin', expected=client_acc)
        if active_acc != None:
            self.set_staff_account_checkbox(setting_name='isActive', expected=active_acc)
        if test_acc != None:
            self.set_staff_account_checkbox(setting_name='isTest', expected=test_acc)
        if blind_trial != None:
            self.set_staff_account_checkbox(setting_name='isBlindTrial', expected=active_acc)
        if global_data != None:
            self.set_staff_account_checkbox(setting_name='isGlobalDataAdministrator', expected=test_acc)


        if remove_managers != None:
            if "PM" in remove_managers:
                print('Removing PM')
                self.kendo_multiselect_clear_all("k-input_Patient_Manager")

            if "TM" in remove_managers:
                print('Removing TM')
                self.kendo_multiselect_clear_all("k-input_Treatment_Monitors")

            if "SM" in remove_managers:
                print('Removing SM')
                self.kendo_multiselect_clear_all("k-input_Site_Managers")

            if "SS" in remove_managers:
                print('Removing SS')
                self.kendo_multiselect_clear_all("k-input_Staff_Administrators")

        time.sleep(3)
        return (new_fname, new_lname) if name_change else (None, None)

    def set_staff_account_checkbox(self, setting_name, expected: bool):
        """Ensure the 'Client Admin' checkbox matches expected state."""
        current = self.is_checked(setting_name)

        # Toggle only if the state is incorrect
        if current != expected:
            self.click(setting_name)

        # Final assertion
        assert self.is_checked(setting_name) == expected, \
            f"{setting_name} checkbox state mismatch. Expected={expected}, Found={self.is_checked(setting_name)}"

        print(f"{setting_name} is {'selected' if expected else 'not selected'}")

    def save_changes(self):
        self.click('button_SUBMIT')
        time.sleep(2)
        try:
            self.kendo_dialog_wait_open()
            text = self.kendo_dialog_get_text()
            print(text)
            self.kendo_dialog_click_button("Yes")
            self.kendo_dialog_wait_close()
            self.wait_for_overlays_to_clear(5)
        except:
            print("No dialog present")
        self.wait_for_invisible('button_SUBMIT')

    def verify_presence_of_save_button(self, presence=True):
        if presence:
            assert self.is_element_present('button_SUBMIT'), "Cannot save changes"
            print("Changes can be saved")
        else:
            assert not self.is_element_present('button_SUBMIT'), "Changes can be saved"
            print("Cannot save changes")