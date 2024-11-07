#!/bin/bash

for i in  100 200 300 400 500 600 700 800 900 1000 1200; do
./deploytpcw_txmud_redblue.sh reset
./deploytpcw_txmud_redblue.sh mysql_reset_clock
./deploytpcw_txmud_redblue.sh coordinator_start
./deploytpcw_txmud_redblue.sh storageshim_start
sleep 60
./deploytpcw_txmud_redblue.sh tomcat_start
./deploytpcw_txmud_redblue.sh user_start $i
./deploytpcw_txmud_redblue.sh get
done;
