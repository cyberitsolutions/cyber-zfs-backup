# Configuration constants for zbm.

import os

#BACKUP_BASE_DIR = '/opt/backup'
BACKUP_BASE_DIR = os.path.join(os.path.abspath('.'), "test/backup")

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
#RESTORE_BASE_DIR = '/opt/restore'
RESTORE_BASE_DIR = os.path.join(os.path.abspath('.'), "test/restore")

# The restore URL for a company should map directly to that company's
# restore directory (as described above).
#
# Appending a slash and the company name to the restore "base" URL
# below will give the company-specific restore URL. Further appending
# a / plus restore tarball/zipfile name (ie. restore-file) will make
# a downloadable URL.
RESTORE_BASE_URL = "https://zhug.cyber.com.au/restore"

# The snapshot dir of a company share should be accessed like so:
#
# os.path.join(BACKUP_BASE_DIR, company_name, share_name, SNAPSHOT_DIR)
SNAPSHOT_DIR = '.zfs/snapshot'

