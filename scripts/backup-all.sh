#!/bin/sh

cd /tank/hosted-backup
rm -f z-backup-all.{out,err}
# config files containing RSA private keys for rsync+ssh clients
for conf in $(cd config && grep -l -- '-----BEGIN RSA PRIVATE KEY-----' *)
do
  ./bin/backup-share.pl $conf >> z-backup-all.out 2>> z-backup-all.err
done
for legacy_conf in $(cd config-legacy && ls -1)
do
  ./bin/backup-share-legacy.pl "$legacy_conf" >> z-backup-all-legacy.out 2>> z-backup-all-legacy.err
done
mv backups/*/*.{out,err} logs
