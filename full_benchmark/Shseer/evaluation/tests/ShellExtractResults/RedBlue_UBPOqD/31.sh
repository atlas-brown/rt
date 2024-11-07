#!/bin/bash

for i in 600 700 800 900 1000 1250 1500 1750 2000 3000 4000; do
./deploytpcw_txmud_allblue.sh reset
./deploytpcw_txmud_allblue.sh mysql_reset_clock
./deploytpcw_txmud_allblue.sh coordinator_start
./deploytpcw_txmud_allblue.sh storageshim_start
sleep 120
./deploytpcw_txmud_allblue.sh tomcat_start
./deploytpcw_txmud_allblue.sh user_start $i
./deploytpcw_txmud_allblue.sh get
done;
