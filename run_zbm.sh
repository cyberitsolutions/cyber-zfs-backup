#!/bin/bash

export LD_LIBRARY_PATH=/usr/postgres/8.2/lib:$LD_LIBRARY_PATH

exec ./zbm

