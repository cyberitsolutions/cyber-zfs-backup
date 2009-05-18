
# Functionality for sending email.

import zbm_cfg as cfg
import smtplib

def send_email(from_address, visible_addresses, subject, content, actual_addressees=None):
    if actual_addressees is None:
        actual_addressees = visible_addresses
    message = """\
From: %s
To: %s
Subject: %s

%s
""" % (from_address, ", ".join(visible_addresses), subject, content)
    server = smtplib.SMTP(cfg.SMTP_SERVER)
    server.sendmail(from_address, actual_addressees, message)
    server.quit()

