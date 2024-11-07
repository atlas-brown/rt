#!/bin/bash

for i in  25 40 50 60 70 80 90 100 200 300 400 500; do
./deploy_tpcw.sh shutdown
./deploy_tpcw.sh reset_database
./deploy_tpcw.sh start_mysql
./deploy_tpcw.sh start_tomcat
./deploy_tpcw.sh start_user $i
./deploy_tpcw.sh wait_for_users_to_finish
./deploy_tpcw.sh get
done;
