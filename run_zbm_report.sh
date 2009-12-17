#!/bin/bash

export LD_LIBRARY_PATH=/usr/postgres/8.2/lib:$LD_LIBRARY_PATH

cd /export/home/cyber/src/zbm

header=zbm_report_header.txt
steve=""
if [ -n "$1" ]; then
    steve="steve"
    header=zbm_report_header_steve.txt
fi

./zbm_report $steve 2> /dev/null | cat "$header" - | mail hosted-backups@cybersource.com.au

