#!/bin/bash

# The zbm database name.
DB_NAME="zbm"

# User responsible for creating zbm database.
SUPER_USER="pete"

# Grant all necessary privileges to the zbm user.
ZBM_USER="zbm"

# Table on which to grant necessary privileges.
TABLES="companies shares users restores restore_files"

for table in $TABLES ; do
    echo "grant all privileges on $table to $ZBM_USER;" | psql -U $SUPER_USER $DB_NAME
done

