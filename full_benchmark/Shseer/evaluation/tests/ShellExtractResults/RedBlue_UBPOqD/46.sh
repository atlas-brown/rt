#!/bin/bash

for i in  25 50 75 100 200 300 400 500 600 ; do
./deploy_tpcw.sh shutdown
./deploy_tpcw.sh install_all
./deploy_tpcw.sh website
./deploy_tpcw.sh configure
./deploy_tpcw.sh reset_database
./deploy_tpcw.sh start_mysql
./deploy_tpcw.sh start_coordinator
sleep 10
#compute magic number
nshims=`echo "$i*2/1" | bc`
./deploy_tpcw.sh start_storageshim $nshims
./deploy_tpcw.sh wait_for_storageshim
sleep 10
./deploy_tpcw.sh start_tomcat
sleep 15
./deploy_tpcw.sh start_user $i
sleep 10
./deploy_tpcw.sh wait_for_users_to_finish
sleep 10
./deploy_tpcw.sh get
done;
