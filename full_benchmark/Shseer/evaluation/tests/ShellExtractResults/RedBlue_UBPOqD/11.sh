#!/bin/bash

for i in  25 50 75 100 200 300 400 500 600 ; do
./deploy_tpcw-mysql-multi-browsing.sh shutdown
./deploy_tpcw-mysql-multi-browsing.sh reset_database
./deploy_tpcw-mysql-multi-browsing.sh start_mysql
sleep 10
./deploy_tpcw-mysql-multi-browsing.sh start_tomcat
sleep 10
./deploy_tpcw-mysql-multi-browsing.sh start_user $i
sleep 10
./deploy_tpcw-mysql-multi-browsing.sh wait_for_users_to_finish
sleep 10
./deploy_tpcw-mysql-multi-browsing.sh get
done;
