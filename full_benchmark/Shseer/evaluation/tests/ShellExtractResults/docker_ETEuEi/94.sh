#!/bin/sh

. /opt/mysql-bootstrap/common.sh

echo " >> Waiting for MySQL to start"

nc -z $MYSQL_PORT_3306_TCP_ADDR $MYSQL_PORT_3306_TCP_PORT -w1
while [ $? -eq 1 ]
do
    nc -z $MYSQL_PORT_3306_TCP_ADDR $MYSQL_PORT_3306_TCP_PORT -w1
done

cp -a /test/sql.d/ /tmp/mysql-bootstrap-sql.d
gzip /tmp/mysql-bootstrap-sql.d/test_gz.sql
bzip2 /tmp/mysql-bootstrap-sql.d/test_bz2.sql
xz /tmp/mysql-bootstrap-sql.d/test_xz.sql

echo " >> Bootstrapping with test.sql file"
DATABASE=bstest1 DATABASE_SQL=/test/test.sql /opt/mysql-bootstrap/init
echo " >> Bootstrapping with sql.d directory"
DATABASE=bstest2 DATABASE_SQL=/tmp/mysql-bootstrap-sql.d /opt/mysql-bootstrap/init

cd /test
exec /test/run
