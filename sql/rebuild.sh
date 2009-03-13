#!/bin/bash

# Configuration.
. ./db-cfg.sh

# Drop and re-create database.
dropdb -U $SUPER_USER $DB_NAME
createdb -U $SUPER_USER $DB_NAME

# Set up tables and initial data.
psql -U $SUPER_USER -f db.sql $DB_NAME
psql -U $SUPER_USER -f db-data.sql $DB_NAME

# Grant privileges to the zbm user.
./grant.sh

