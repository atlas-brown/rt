#!/bin/bash

for i in 100 200 300 400 500 600 700 800 900 1000 1200 ; do
./deploytpcw_mysql.sh reset
./deploytpcw_mysql.sh mysql_start
sleep 10
./deploytpcw_mysql.sh tomcat_start
./deploytpcw_mysql.sh user_start $i
./deploytpcw_mysql.sh get
done;
