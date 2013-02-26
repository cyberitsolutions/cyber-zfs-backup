#!/bin/bash

export LD_LIBRARY_PATH=/usr/postgres/8.2/lib:$LD_LIBRARY_PATH

cd /export/home/cyber/src/zbm

header=bandwidth_report_header.txt

./restore_bandwidth_report 2> /dev/null | cat "$header" - | mail support-DatasafeR@cyber.com.au

