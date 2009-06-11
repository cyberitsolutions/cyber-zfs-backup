#!/bin/sh

cd /tank/hosted-backup
rm -f z-backup-all.{out,err}
# config files containing RSA private keys for rsync+ssh clients
for conf in $(cd config && grep -l -- '-----BEGIN RSA PRIVATE KEY-----' *)
do
  ./bin/backup-share.pl $conf >> z-backup-all.out 2>> z-backup-all.err
done
mv backups/*/*.{out,err} logs
