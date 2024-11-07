#!/bin/sh

if [ -z "$MYSQL_TAG" ]
then
    MYSQL_TAG='alreece45/phusion-mysql:latest'
fi

if [ -z "$TAG" ]
then
    TAG='alreece45/ubuntu-mysql-bootstrap:latest'
fi

PWD=`dirname $0`

echo " >> Starting MySQL Container"
mysql_cid=`docker run -d \
    -e ADMIN_USER=admin \
    -e ADMIN_PASS=mysql-bootstrap \
    $MYSQL_TAG`
mysql_name=`docker inspect --format='{{.Name}}' $mysql_cid`

echo " >> Starting Bootstrap Container"
docker run \
    --rm=true \
    --link $mysql_name:mysql \
    -v $PWD/test:/test \
    -e MYSQL_USER=admin \
    -e MYSQL_PWD=mysql-bootstrap \
    -e DATABASE=bstest1 \
    -e DATABASE_USER=bstest2 \
    -e DATABASE_PASS=bstest3 \
    $TAG \
    /test/init

boostrap_result=$?

echo " >> Cleaning up MySQL Container $mysql_cid"
docker stop $mysql_cid > /dev/null
docker rm $mysql_cid > /dev/null

exit $bootstrap_result
