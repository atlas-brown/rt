#!/bin/bash

for i in  25 50 75 100 200 300 400 500; do
./deploy_tpcw-mysql-single-ordering.sh shutdown
./deploy_tpcw-mysql-single-ordering.sh reset_database
./deploy_tpcw-mysql-single-ordering.sh start_mysql
sleep 10
./deploy_tpcw-mysql-single-ordering.sh start_tomcat
sleep 10
./deploy_tpcw-mysql-single-ordering.sh start_user $i
sleep 10
./deploy_tpcw-mysql-single-ordering.sh wait_for_users_to_finish
sleep 10
./deploy_tpcw-mysql-single-ordering.sh get
done;
