#!/bin/bash
#
# Filename: apply_schema_revision.sh
#
# Usage:
#
#   ./apply_schema_revision.sh revisions/00001-do-something-to-database.sql
#
# Description:
#
# Loads a file of given format into configured-target PostgreSQL database,
# if-and-only-if all conditions are met.
#
# Note: Inserts/updates/deletes should be rolled back, but table
# creates/drops will **NOT** be rolled back. If the supplied
# "revision" SQL file is broken and fails, it's the user's
# responsibility to clean up the mess.

# Get DB-access config.
. ./zbm_cfg.sh

######################################################################
# Get current revision of DB.
function get_current_revision {
  echo "select coalesce(max(revision_number), 0) from db_revision;" | \
    psql -A --username "$DBUSER" --host "$DBHOST" --port "$DBPORT" --dbname "$DBNAME" | \
    tail -n +2 | \
    head -n 1
}

######################################################################
# Check command-line arg.

REVISION_SQL_FILENAME="$1"

if [ -z "$REVISION_SQL_FILENAME" ]; then
  echo "Usage: $0 00001-an-sql-file-to-apply-to-database.sql"
  exit 1
fi

if [ ! -r "$REVISION_SQL_FILENAME" ]; then
  echo "Can't read file \"$REVISION_SQL_FILENAME\"."
  exit 1
fi

# Check that it's a valid revision filename.
rev_basename=`basename "$REVISION_SQL_FILENAME"`

# Single-quotes explicitly disallowed.
echo "$rev_basename" | grep -q "^[0-9]\{5\}-[^']*\.sql\$" || ( echo "Invalid revision filename $rev_basename." ; exit 1 )

revno=`echo "$rev_basename" | sed 's/^\([0-9]\{5\}\)-.*$/\1/'`

DB_CURRENT_REVNO=`get_current_revision`
DB_EXPECTED_REVNO=`expr 1 + $DB_CURRENT_REVNO`

if [ $revno -ne $DB_EXPECTED_REVNO ]; then
  echo "Cannot apply $REVISION_SQL_FILENAME to current DB, expected revision number $DB_EXPECTED_REVNO."
  exit 1
fi

######################################################################
# Okay, we can apply the revision SQL file. Rock and roll.

( \
  echo "start transaction;"; \
  cat "$REVISION_SQL_FILENAME"; \
  echo "insert into db_revision ( revision_number, filename, applied_datetime ) values ( $revno, '$rev_basename', now() );";
  echo "commit;"; \
) | \
    psql --username "$DBUSER" --host "$DBHOST" --port "$DBPORT" --dbname "$DBNAME" && \
    echo "Applied revision $revno." || \
    echo "ERROR: Failed to apply revision $revno."

