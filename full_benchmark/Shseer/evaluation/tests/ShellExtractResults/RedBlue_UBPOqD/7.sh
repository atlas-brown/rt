#!/bin/bash

for i in 40 50 60 70 80 90 100 200 300 400 500 600 700 800 ; do
./deploy_tpcw.sh shutdown
./deploy_tpcw.sh reset_database
./deploy_tpcw.sh start_mysql
./deploy_tpcw.sh start_coordinator

#compute magic number
nshims=`echo "$i*2/1" | bc`
./deploy_tpcw.sh start_storageshim $nshims
./deploy_tpcw.sh wait_for_storageshim
echo "all storage shims are ok"
./deploy_tpcw.sh start_tomcat

./deploy_tpcw.sh start_user $i
./deploy_tpcw.sh wait_for_users_to_finish
./deploy_tpcw.sh get
done;

