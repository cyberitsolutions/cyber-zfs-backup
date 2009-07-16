#!/bin/sh

# set field seperator to a single newline (so remove the default tab and
# space char seperators which mess up the loops below)
IFS=$'\n'

cd /tank/hosted-backup
rm -f z-backup-output.txt
# config files containing RSA private keys for rsync+ssh clients
for conf in $(cd config && grep -l -- '-----BEGIN RSA PRIVATE KEY-----' *)
do
  ./bin/backup-share.pl "$conf" 2>&1 >> z-backup-output.txt
done
for legacy_conf in $(cd config-legacy && ls -1)
do
  ./bin/backup-share-legacy.pl "$legacy_conf" 2>&1 >> z-backup-output.txt
done

(cat z-backup-output.txt; head -100 backups/*/*.err) | /usr/bin/mailx -s 'zhug backup logs' hosted-backups@cybersource.com.au

mv backups/*/*.{out,err} logs
