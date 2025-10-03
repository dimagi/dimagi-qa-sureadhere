import time

from common_utilities.base_page import BasePage
from common_utilities.generate_random_string import fetch_random_string
from user_inputs.user_data import UserData


class UserStaffPage(BasePage):
    first_name_text = "test_first_" + fetch_random_string()
    last_name_text = "test_last_" + fetch_random_string()
    email = fetch_random_string() + "@testmail.com"

    def __init__(self, sb, page_name):
        super().__init__(sb, page_name=page_name)


    def fill_staff_form(self, site_manager):
        self.type('first_name', self.first_name_text)
        self.type('last_name', self.last_name_text)
        self.type('email', self.email)
        self.type('password', UserData.pwd)
        self.type('phone_number', UserData.phone_number)

        self.click('selectedPatientManagers')
        self.kendo_select("k-input_Patient_Manager", text=site_manager)
        self.kendo_select("k-input_Patient_Manager", text=site_manager)
        self.kendo_select_first("k-input_Patient_Manager")

        self.click('selectedTreatmentMonitors')
        self.kendo_select("k-input_Treatment_Monitors", text=site_manager)
        self.kendo_select("k-input_Treatment_Monitors", text=site_manager)
        self.kendo_select_first("k-input_Treatment_Monitors")

        self.click('selectedSiteManagers')
        self.kendo_select("k-input_Site_Managers", text=site_manager)
        self.kendo_select("k-input_Site_Managers", text=site_manager)
        self.kendo_select_first("k-input_Site_Managers")

        self.click('selectedStaffAdministrators')
        self.kendo_select("k-input_Staff_Administrators", text=site_manager)
        self.kendo_select("k-input_Staff_Administrators", text=site_manager)
        self.kendo_select_first("k-input_Staff_Administrators")

        self.click('isClientAdmin')
        assert self.is_checked('isClientAdmin'), "Client Admin not checked"

        self.click('isRegimenEditor')
        assert self.is_checked('isRegimenEditor'), "Regimen Editor not checked"

        self.click('button_SUBMIT')
        self.wait_for_invisible('button_SUBMIT')
        client=True

        print(f"Staff Created: {self.first_name_text}, {self.last_name_text}, {self.email}, {UserData.phone_number}")
        return self.first_name_text, self.last_name_text, self.email, UserData.phone_number, client, site_manager

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



