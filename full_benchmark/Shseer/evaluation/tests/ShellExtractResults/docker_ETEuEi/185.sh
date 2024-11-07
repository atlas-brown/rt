#!/bin/sh
cd `dirname $0`

# Configure postfix to start as a service
mkdir /etc/service/postfix
cp -a ./service.sh /etc/service/postfix/run
chmod +x /etc/service/postfix/run
