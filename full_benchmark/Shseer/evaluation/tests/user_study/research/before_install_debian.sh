#!/bin/bash

echo "Start"

alias wanip='dig +short myip.opendns.com @resolver1.opendns.com'
alias su_as='su --shell=/bin/bash - '
alias tab2space='expand -i -t 1'
alias rims_reload='/etc/init.d/rims restart'
alias rims_clear='/etc/init.d/rims clear'
alias rims_mysql='mysql -urims -prims rims'

apt-get install sudo nano net-tools git python3 python3-pip mariadb-server mariadb-client libsnmp-dev libxslt-dev

# Graphviz for ERD
apt-get install -y graphviz graphviz-dev

# Grafana & Influxdb
apt-get install -y influxdb influxdb-client
apt-get install -y apt-transport-https
apt-get install -y software-properties-common wget
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb [trusted=yes] https://packages.grafana.com/oss/deb stable main" >> /etc/apt/sources.list
apt-get update
apt-get upgrade
systemctl daemon-reload
systemctl start grafana-server
systemctl status grafana-server

pip3 install pymysql
pip3 install dnspython
pip3 install python3-netsnmp
pip3 install paramiko
pip3 install gitpython
pip3 install pyVmomi
pip3 install junos-eznc
pip3 install graphviz

cd /usr/local/sbin
git init
git clone git@github.com:zelbanna/rims.git
git clone http://github.com/azlux/log2ram.git
cd
ln -s /usr/local/sbin/rims
cd rims
