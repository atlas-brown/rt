#!/bin/sh
cd `dirname $0`
. ./ubuntu-setup.sh

# Configure mysql to start as a service
mkdir /etc/service/mysql
cp -a ./service.sh /etc/service/mysql/run
chmod +x /etc/service/mysql/run
