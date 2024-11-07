#!/bin/sh

PWD=`pwd`

if [ -z "$TAG" ]
then
    TAG='alreece45/phusion-mysql-bootstrap:trusty'
fi

exec env TAG="$TAG" $PWD/ubuntu_trusty/test.sh
