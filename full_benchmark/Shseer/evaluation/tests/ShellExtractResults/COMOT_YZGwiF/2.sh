#!/bin/bash

echo "tomcat deploy"

wget -q http://128.130.172.215/salsa/upload/files/juraj/elasticWS/artifactTomcat-1.0.tar.gz
tar -xzf ./artifactTomcat-1.0.tar.gz
cd ./artifactTomcat

sudo chmod +x migrate.sh
sudo chmod +x post_migrate.sh
sudo chmod +x pre_migrate.sh
sudo chmod +x undeploy.sh

sudo apt-get update
# install and start tomcat
sudo apt-get install tomcat7 -y
# install manager
sudo apt-get install tomcat7-admin -y
# set user access rights
sudo cp ./tomcat-users.xml /etc/tomcat7/tomcat-users.xml
# restart to register new user-settings
sudo service tomcat7 restart

# wait until tomcat is ready
curl "http://comot:comot@localhost:8080/manager/text/list"