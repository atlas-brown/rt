#!/bin/bash

echo "war undeploy"

curl "http://comot:comot@localhost:8080/manager/text/undeploy?path=/testWS"

cd ..
rm -rf artifactWar
rm artifactWar-1.0.tar.gz