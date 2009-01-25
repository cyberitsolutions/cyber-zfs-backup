#!/bin/bash

# Configuration.
. ./db-cfg.sh

# Drop and re-create database.
dropdb $DB_NAME
createdb $DB_NAME

# Set up tables and initial data.
psql -U $SUPER_USER $DB_NAME < db.sql
psql -U $SUPER_USER $DB_NAME < db-data.sql

# Grant privileges to the zbm user.
./grant.sh

