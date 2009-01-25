#!/bin/bash

# Configuration.
. ./db-cfg.sh

# Table on which to grant necessary privileges.
TABLES="companies shares users restores restore_files"

for table in $TABLES ; do
    echo "grant all privileges on $table to $ZBM_USER;" | psql -U $SUPER_USER $DB_NAME
done

