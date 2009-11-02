#!/bin/bash

export LD_LIBRARY_PATH=/usr/postgres/8.2/lib:$LD_LIBRARY_PATH

cd /export/home/cyber/src/zbm

./zbm_report 2> /dev/null | cat zbm_report_header.txt - | mail hosted-backups@cybersource.com.au

