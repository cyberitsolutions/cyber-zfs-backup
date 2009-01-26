
import os
# Configuration constants for zbm.

#BACKUP_BASE_DIR = '/opt/backup'
BACKUP_BASE_DIR = os.path.join(os.path.abspath('.'), "test/backup")

#RESTORE_BASE_DIR = '/opt/restore'
RESTORE_BASE_DIR = os.path.join(os.path.abspath('.'), "test/restore")

# The snapshot dir of a company share should be accessed like so:
# os.path.join(BACKUP_BASE_DIR, company_name, share_name, SNAPSHOT_DIR)
SNAPSHOT_DIR = '.zfs/snapshot'

