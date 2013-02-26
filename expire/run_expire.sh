#!/bin/bash

#set -x

expire="/tank/hosted-backup/bin/expire.py"
remove="/tank/hosted-backup/bin/remove.sh"

if [ -n "$1" ]
then
    dry_run="true"
fi

for backup in /tank/hosted-backup/config-aging/*
do
    #share=`basename "$backup" .pub`
    share="$backup"
    company=`basename $share | cut -d: -f1`
    path=`echo $share | cut -d@ -f2`

    dailies=-1
    weeklies=-1
    monthlies=-1
    yearlies=-1

    . $backup
    echo "$backup"
    echo "$dailies" -eq -1 -o "$weeklies" -eq -1 -o "$monthlies" -eq -1 -o "$yearlies" -eq -1

    if [ "$dailies" -eq -1 -o "$weeklies" -eq -1 -o "$monthlies" -eq -1 -o "$yearlies" -eq -1 ]
    then
        true # Error message?
        echo blah
    else
        share_root=/tank/hosted-backup/backups/$company/$path
        full_path="$share_root/.zfs/snapshot"
        if [ -n "$dry_run" ]
        then
            echo "full_path: $full_path company $company path $path"
            $expire -v $full_path $dailies $weeklies $monthlies $yearlies
        else
            $expire $full_path $dailies $weeklies $monthlies $yearlies | xargs -L 1 echo $remove $share_root
       fi
    fi

done

