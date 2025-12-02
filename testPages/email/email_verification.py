import datetime
import time

from imap_tools import MailBox
from imap_tools import AND, OR, NOT
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import timedelta

from user_inputs.user_data import UserData

""""Contains test page elements and functions related to the app installation and form submission on mobile"""


class EmailVerification:

    def __init__(self, settings):
        self.imap_host = "imap.gmail.com"
        self.imap_user = UserData.reset_email_address
        self.imap_pass = settings['sa_imap_password']

    def get_verification_code_from_email(self, subject, target_email):
        code_re = re.compile(r'\b(\d{4,8})\b')
        # cutoff = datetime.now() - timedelta(minutes=45)
        from_email=UserData.sureadhere_from

        print(f"Subject to be fetched: {subject}")

        with MailBox(self.imap_host).login(self.imap_user, self.imap_pass, 'INBOX') as mailbox:
            msgs = list(mailbox.fetch(
            AND(subject=subject, from_=from_email, date=datetime.date.today()), reverse=True))
            if not msgs:
                print("⚠️ No emails found for the subject/sender.")
                return None

            for msg in msgs:  # iterate newest first
                html_body = msg.html or ""
                soup = BeautifulSoup(html_body, "html.parser")

                # Check if the HTML body actually mentions the target email
                if target_email.lower() not in soup.get_text().lower():
                    continue  # skip this one; likely the other environment's email

                # Find the verification text spans
                mailto_span = soup.find("span", id=re.compile("UserVerificationEmailBodySentence1"))
                code_span = soup.find("span", id=re.compile("UserVerificationEmailBodySentence2"))

                if code_span:
                    match = code_re.search(code_span.text)
                    if match:
                        actual_code = match.group(1).strip()
                        print(f"✅ Found code {actual_code} for {target_email}")
                        return actual_code

            print(f"⚠️ No matching email body found containing {target_email}")
            return None