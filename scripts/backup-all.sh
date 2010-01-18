#!/bin/sh

# set field seperator to a single newline (so remove the default tab and
# space char seperators which mess up the loops below)
IFS=$'\n'

cd /tank/hosted-backup
rm -f z-backup-output.txt

# nuke any existing rsync processes
# XXX this sucks, and should only be killing *our* rsync processes, but
# XXX since we don't save their PIDs we just hit everything with a rock.
/usr/bin/pkill rsync; sleep 30; /usr/bin/pkill -9 rsync

# config files containing RSA private keys for rsync+ssh clients
for conf in $(cd config && grep -l -- '-----BEGIN RSA PRIVATE KEY-----' *)
do
  ./bin/backup-share.pl "$conf" 2>&1 >> z-backup-output.txt &
done
# config files containing rsync passwords for pure rsync clients
for legacy_conf in $(cd config-legacy && ls -1)
do
  ./bin/backup-share-legacy.pl "$legacy_conf" 2>&1 >> z-backup-output.txt &
done

wait

(cat z-backup-output.txt; head -100 backups/*/*.err) | /usr/bin/mailx -s 'zhug backup logs' hosted-backups@cybersource.com.au

mv backups/*/*.{out,err} logs
