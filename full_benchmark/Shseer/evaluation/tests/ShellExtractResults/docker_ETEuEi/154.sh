#!/bin/bash

cd `dirname $0`

# Update sources and install packages
. ./common-debian-packages/preinstall.sh
apt-get --no-install-recommends -y install mysql-client
. ./common-debian-packages/postinstall.sh

