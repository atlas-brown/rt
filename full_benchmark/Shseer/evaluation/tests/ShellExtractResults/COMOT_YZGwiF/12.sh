#!/bin/bash

echo "rsybl deploy"

wget -q http://128.130.172.215/salsa/upload/files/juraj/dynamic_eps/rsybl.tar.gz
tar -xzf ./rsybl.tar.gz
cd ./rsybl

sudo chmod +x rSYBL-service

sudo ./rSYBL-service start

# wait until ready
#curl "http://localhost:8180/MELA/"