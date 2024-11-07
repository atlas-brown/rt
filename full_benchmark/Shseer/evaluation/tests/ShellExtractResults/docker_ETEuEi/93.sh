#!/bin/sh

PWD=`pwd`

if [ -z "$TAG" ]
then
    TAG='alreece45/phusion-mysql-bootstrap:latest'
fi

exec env TAG="$TAG" MYSQL_TAG="$MYSQL_TAG" $PWD/ubuntu_trusty/test.sh
