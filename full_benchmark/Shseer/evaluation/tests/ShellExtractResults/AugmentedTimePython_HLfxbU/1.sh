#!/bin/sh

sudo apt-get -q -y install automake autoconf g++ gcc make libtool ntp
if [ $? -ne 0 ] ; then
echo "installing packages failed";
fi

export LD_LIBRARY_PATH=`pwd`/lib;
export AWS_HOME=`pwd`;


