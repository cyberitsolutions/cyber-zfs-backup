#!/bin/bash

# Configuration.
. ./db-cfg.sh

# Table on which to grant necessary privileges.
TABLES="companies shares users restores restore_files"
SEQUENCES="restores_id_seq shares_id_seq"

for item in $TABLES $SEQUENCES ; do
    echo "grant all privileges on $item to $ZBM_USER;" | psql -U $SUPER_USER $DB_NAME
done

