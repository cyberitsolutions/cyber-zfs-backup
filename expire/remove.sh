#!/bin/bash


if [ $# -lt 2 ]
then
	cat <<EOF
usage: $0 <path> <snapshot>
	path		The root of the share
	snapshot	The specific snapshot to remove

'path' will usually end at hostname:path. Snapshot will only be a single
timestamp. Do not include the '.zfs/snapshot/' in between.
EOF
	exit 1
fi

. /export/home/cyber/src/zbm/sql/zbm_cfg.sh

psql=/usr/postgres/8.2/bin/psql

path=$1
snapshot=$2

# $1 is base path (up to :share), $2 is the snapshot itself

# Base path for snapshots is $hosted_backup_backups_fs/$client/$source_host:$source_path_colon
# hosted_backup_backups_fs is /tank/hosted-backup/backups/
# so zfs destroy /tank/hosted-backup/backups/$client/$host_blah@timestamp

full_path="${path}/.zfs/snapshot/${snapshot}"

# db path is /tank/hosted-backup/backups/insightsrc/mail.insightsrc.com.au:srv:share/.zfs/snapshot/2010-11-18T14:05:08Z
# Let the FK ON DELETE CASCADE do the hard work
echo "DELETE FROM filesystem_info WHERE path = '${full_path}';" | $psql -A --username "$DBUSER" --host "$DBHOST" --port "$DBPORT" --dbname "$DBNAME"
echo "DELETE FROM filesystem_info WHERE path = '${full_path}';" 
# zfs doesn't want the leading /
zfs_path=`echo $path | sed 's|^/||'`

zfs destroy "${zfs_path}@${snapshot}"
echo "${zfs_path}@${snapshot}"
