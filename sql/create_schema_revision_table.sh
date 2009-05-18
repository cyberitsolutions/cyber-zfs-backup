#!/bin/bash

# Get DB-access config.
. ./zbm_cfg.sh

# Create the revision table.
psql --username $DBUSER --host $DBHOST --port $DBPORT --dbname $DBNAME \
  --command "create table db_revision ( revision_number integer primary key, filename text not null, applied_datetime datetime not null )"

