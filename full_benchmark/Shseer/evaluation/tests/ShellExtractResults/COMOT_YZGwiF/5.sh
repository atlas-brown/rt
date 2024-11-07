#!/bin/bash

echo "tomcat undeploy"

sudo apt-get -y erase tomcat7
sudo apt-get -y erase tomcat7-admin

cd ..
rm -rf artifactTomcat
rm artifactWar-1.0.tar.gz