# Configuration constants for zbm.

import os

# The explicit absolute path to a GNU du(1).
# Specifically we require one that accepts -b and -s flags.
GNU_DU_PATH = '/usr/gnu/bin/du'

BACKUP_BASE_DIR = '/tank/hosted-backup/backups'
#BACKUP_BASE_DIR = os.path.join(os.path.abspath('.'), "test/backup")

# The restore directory for a company should be accessed like so:
#
# os.path.join(RESTORE_BASE_DIR, company_name)
#
# There is no separation by share as a restore tarball or zipfile can
# contain stuff from any snapshot of any share of that company.
#
# Each company's restore directory should have its own .htaccess file,
# referring to a htdigest password file and specifying that only users
# of the "group" (directly corresponding to company) can access the
# contents of the directory. That is an Apache configuration detail
# and outside the scope of ZBM itself.
#
# Also outside of ZBM's scope - an external cron script(?) is expected
# to handle removing restore-files when they are no longer wanted,
# where "no longer wanted" is a fairly flexible definition (eg. older
# than 24 hours?).
RESTORE_BASE_DIR = '/tank/hosted-backup/restores'
#RESTORE_BASE_DIR = os.path.join(os.path.abspath('.'), "test/restore")

# The restore URL for a company should map directly to that company's
# restore directory (as described above).
#
# Appending a slash and the company name to the restore "base" URL
# below will give the company-specific restore URL. Further appending
# a / plus restore tarball/zipfile name (ie. restore-file) will make
# a downloadable URL.
RESTORE_BASE_PATH = "/restore"
RESTORE_BASE_URL = "https://cybersource.com.au"
RESTORE_BASE_URL_PATH = RESTORE_BASE_URL + RESTORE_BASE_PATH

# Backup base URL.
BACKUP_BASE_PATH = "/backup"
BACKUP_BASE_URL = "https://cybersource.com.au"
BACKUP_BASE_URL_PATH = BACKUP_BASE_URL + BACKUP_BASE_PATH

# The snapshot dir of a company share should be accessed like so:
#
# os.path.join(BACKUP_BASE_DIR, company_name, share_name, SNAPSHOT_DIR)
SNAPSHOT_DIR = '.zfs/snapshot'

# SMTP server for use by ZBM in sending email.
SMTP_SERVER = 'localhost'

# The official Cybersource email address(es) to which ZBM may need to
# send particular types of notification messages.
FROM_EMAIL_ADDRESS = 'Hosted Backups <hosted-backups@cybersource.com.au>'
SUPPORT_EMAIL_ADDRESS = 'support@cybersource.com.au'
ACCOUNTS_EMAIL_ADDRESS = 'accounts@cybersource.com.au'

# The official Cybersource email address to which ZBM will send a copy
# of *every* download-notification email sent to a customer.
#NOTIFY_CC_EMAIL_ADDRESS = 'hosted-backups@cybersource.com.au'
NOTIFY_CC_EMAIL_ADDRESS = 'jeremyc@cybersource.com.au'

# Email templates.
#
# There's probably a better place to put these, but I'll
# put them here for the time being.
COMPANY_FILE_DOWNLOAD_TEMPLATE = """
Cybersource Hosted Backup Service

%(human_readable_datetime)s

User %(username)s (%(full_name)s) is downloading the following restore file,
which is %(download_file_size)s in size:

  %(download_url)s

This link will remain valid for 48 hours.

This is not a bill for payment. You will be invoiced for this download
after the end of the month.

Thank you for using the Cybersource Hosted Backup service.

Regards,

Cybersource Pty Ltd
Email: info@cybersource.com.au
Phone: +61 3 9428 6922
Fax:   +61 3 9428 6944
"""

CYBERSOURCE_ACCOUNTS_DOWNLOAD_TEMPLATE = """
"""

MANUAL_RESTORE_TEMPLATE = """

%(human_readable_datetime)s

User %(username)s (%(full_name)s) of company %(company)s has requested physical
media for a restore. The file list is available at:
%(filename)s

"""

# The number of records to display on pages that get ... paged (i.e.,
# pages that have Next/Prev and "Page X of Y" on them).
DEFAULT_PAGE_SIZE = 20

# The maximum size of restore archives (before compression) that will
# be permitted. Beyond this the customer must ask for physical media
RESTORE_SIZE_LIMIT=250

# What customers should call zbm
ZBM_PRETTY_NAME = 'Datasafe/R'
