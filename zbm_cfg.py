
BACKUP_BASE_DIR = '/opt/backup'

RESTORE_BASE_DIR = '/opt/restore'

# The snapshot dir of a client share should be accessed like so:
# os.path.join(BACKUP_BASE_DIR, client_name, share_name, SNAPSHOT_DIR)
SNAPSHOT_DIR = '.zfs/snapshot'

