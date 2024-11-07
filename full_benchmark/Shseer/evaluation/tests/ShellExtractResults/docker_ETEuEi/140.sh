#!/bin/bash

cd `dirname $0`

# Update sources and install packages
. ./common-debian-packages/preinstall.sh
apt-get --no-install-recommends -y install mysql-server pwgen
. ./common-debian-packages/postinstall.sh

