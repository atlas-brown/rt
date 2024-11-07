#!/bin/bash

#for i in  25 50 75 100 200 300 400 500 600; do
#for i in  100 200 300 400 500 600 700 800 900 1000 1200 1500 2000; do
 for i in  1 2 4 8 16 20 25 30 40 50 75 100 150 200 300 400; do
./deploy_tpcw-mysql-single-shopping.sh shutdown
./deploy_tpcw-mysql-single-shopping.sh install_all
./deploy_tpcw-mysql-single-shopping.sh website
./deploy_tpcw-mysql-single-shopping.sh configure
./deploy_tpcw-mysql-single-shopping.sh reset_database
./deploy_tpcw-mysql-single-shopping.sh start_mysql
sleep 10
./deploy_tpcw-mysql-single-shopping.sh start_tomcat
sleep 10
./deploy_tpcw-mysql-single-shopping.sh start_user $i
sleep 10
./deploy_tpcw-mysql-single-shopping.sh wait_for_users_to_finish
sleep 10
./deploy_tpcw-mysql-single-shopping.sh get
done;
