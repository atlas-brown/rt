#!/bin/bash

echo "war deploy"

wget -q http://128.130.172.215/salsa/upload/files/juraj/elasticWS/artifactWar-1.0.tar.gz
tar -xzf ./artifactWar-1.0.tar.gz
cd ./artifactWar

sudo chmod +x migrate.sh
sudo chmod +x post_migrate.sh
sudo chmod +x pre_migrate.sh
sudo chmod +x undeploy.sh

# e.g. /home/ubuntu
DIR=$(pwd)

echo "DIR: "$DIR

curl "http://comot:comot@localhost:8080/manager/text/deploy?war=file:"$DIR"/testWS-1.0.war&path=/testWS"
