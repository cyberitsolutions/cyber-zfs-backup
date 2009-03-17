#!/bin/bash

# The user/realm/password file used by Squid.
DIGEST_PASSWORD_FILE=/etc/zbm/zbm_passwords

# Note: Password file must be readable by Squid proxy user.
umask 0022
TEMPFILE=`mktemp`

# Command line argument - just the username.
if [ -z "$1" ] ; then
        echo "Usage: $0 user";
        exit 1
fi

USER=$1

# Make sure the file exists.
touch $DIGEST_PASSWORD_FILE

# Crude but effective user-removal.
grep -v "^$USER:" $DIGEST_PASSWORD_FILE > $TEMPFILE && \
cat $TEMPFILE > $DIGEST_PASSWORD_FILE && \
rm -f $TEMPFILE

