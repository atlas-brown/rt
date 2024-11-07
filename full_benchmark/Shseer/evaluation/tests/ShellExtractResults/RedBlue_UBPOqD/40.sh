#!/bin/bash

for i in  50 100 150 200 250 300 350 400 450 500 550 600; do
./deploy_tpcw_txmud_multidc.sh reset
./deploy_tpcw_txmud_multidc.sh mysql_reset_clock
./deploy_tpcw_txmud_multidc.sh mysql_start
./deploy_tpcw_txmud_multidc.sh coordinator_start
./deploy_tpcw_txmud_multidc.sh storageshim_start
sleep 200
./deploy_tpcw_txmud_multidc.sh tomcat_start
./deploy_tpcw_txmud_multidc.sh user_start $i
./deploy_tpcw_txmud_multidc.sh get

done;

