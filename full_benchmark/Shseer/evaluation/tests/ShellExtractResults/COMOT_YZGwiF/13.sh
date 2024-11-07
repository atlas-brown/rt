#!/bin/bash

echo "mela deploy"

wget -q http://128.130.172.215/salsa/upload/files/juraj/dynamic_eps/mela.tar.gz
tar -xzf ./mela.tar.gz
cd ./mela

sudo chmod +x mela-data-service

sudo ./mela-data-service start

# wait until ready
#curl "http://localhost:8180/MELA/"