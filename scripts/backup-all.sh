#!/bin/sh

cd /tank/hosted-backup
rm -f z-backup-all.{out,err}
for conf in $(cd config && ls -1 | egrep -v '\.pub$')
do
  ./bin/backup-share.pl $conf >> z-backup-all.out 2>> z-backup-all.err
done
mv backups/*/*.{out,err} logs
