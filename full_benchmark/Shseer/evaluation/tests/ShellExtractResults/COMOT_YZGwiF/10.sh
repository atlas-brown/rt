#!/bin/bash

echo "war migrate"

wget http://128.130.172.215/salsa/upload/files/juraj/elasticWS/artifactWar-2.0.tar.gz
tar -xzf ./artifactWar-2.0.tar.gz
cd ./artifactWar

curl "http://comot:comot@localhost:8080/manager/text/deploy?war=file:./testWS-0.2.war&path=/testWS"
