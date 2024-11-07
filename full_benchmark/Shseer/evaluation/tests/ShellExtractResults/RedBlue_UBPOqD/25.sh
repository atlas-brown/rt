#!/bin/bash

 for i in 2 4 8 16 20 25 30 40 50 75 100 150 200 300 400; do
./deploy_tpcw-mysql-multi-user-shopping.sh shutdown
./deploy_tpcw-mysql-multi-user-shopping.sh website
./deploy_tpcw-mysql-multi-user-shopping.sh configure
./deploy_tpcw-mysql-multi-user-shopping.sh reset_database
./deploy_tpcw-mysql-multi-user-shopping.sh start_mysql
sleep 10
./deploy_tpcw-mysql-multi-user-shopping.sh start_tomcat
sleep 10
./deploy_tpcw-mysql-multi-user-shopping.sh start_user $i
sleep 10
./deploy_tpcw-mysql-multi-user-shopping.sh wait_for_users_to_finish
sleep 10
./deploy_tpcw-mysql-multi-user-shopping.sh get
done;
