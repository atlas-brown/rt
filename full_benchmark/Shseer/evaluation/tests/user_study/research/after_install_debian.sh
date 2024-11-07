#!/bin/bash
# Standalone server

echo "Starting installation - give root DB password on the next line and press enter"
read mariadbpassword
echo "Continuing"

alias wanip='dig +short myip.opendns.com @resolver1.opendns.com'
alias su_as='su --shell=/bin/bash - '
alias tab2space='expand -i -t 1'
alias rims_reload='/etc/init.d/rims restart'
alias rims_clear='/etc/init.d/rims clear'
alias rims_mysql='mysql -urims -prims rims'

apt-get update
apt-get upgrade
apt-get install -y sudo nano net-tools git python3 python3-pip mariadb-server mariadb-client libsnmp-dev libxslt-dev apt-transport-https ca-certificates curl gnupg-agent software-properties-common

curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian  $(lsb_release -cs) stable"
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io

docker network create --subnet=172.18.0.0/16 services
echo "Creating containers"
echo "MariaDB: 172.18.0.2"
echo "InfluxDB: 172.18.0.3 -> add to config.json"
echo "Grafana: 172.18.0.6 -> proxy to port 3000 locally"
echo "PDNS Recursor: 172.18.0.4 -> configure API and add to config.json, proxy to port 53 locally"
echo "PDNS Server: 172.18.0.5 -> configure API and add to config.json"
echo ""
echo " - press enter to continue - "
read
docker create --name=mariadb -e PUID=1000 -e PGID=1000 -e MYSQL_ROOT_PASSWORD=$mariadbpassword -e TZ=Europe/Stockholm -v mariadb:/config --net services --ip 172.18.0.2 --restart unless-stopped linuxserver/mariadb
docker create --name=influxdb -v influxdb:/var/lib/influxdb --net services --ip 172.18.0.3 --restart unless-stopped influxdb:1.8
docker create --name=grafana -p 3000:3000 -v grafana:/var/lib/grafana --net services --ip 172.18.0.6 --restart unless-stopped grafana/grafana
docker create --name=pdns-recursor -p 53:53 -p 53:53/udp -v pdns-recursor:/etc/powerdns  --net services --ip 172.18.0.4 --restart unless-stopped xddxdd/powerdns-recursor
docker create --name=pdns-server -v pdns-server:/etc/powerdns  --net services --ip 172.18.0.5 --restart unless-stopped xddxdd/powerdns
echo "Create the following backend connection for PowerDNS volume (pdns-server):"
echo " >> pdns.d/pdns.local.gmysql.conf"
echo "launch+=gmysql"
echo "gmysql-host=172.18.0.2"
echo "gmysql-port=3306"
echo "gmysql-dbname=pdns"
echo "gmysql-user=pdns"
echo "gmysql-password=pdns"
echo "gmysql-dnssec=no"
echo ""
echo " - press enter to continue - "
read

pip3 install pymysql
pip3 install dnspython
pip3 install python3-netsnmp
pip3 install paramiko
pip3 install gitpython
pip3 install junos-eznc

cd /usr/local/sbin
git init
git clone git@github.com:zelbanna/rims.git
git clone http://github.com/azlux/log2ram.git
cd
ln -s /usr/local/sbin/rims
cd rims
