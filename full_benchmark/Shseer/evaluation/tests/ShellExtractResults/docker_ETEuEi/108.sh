#!/bin/bash

add_slashes_sq() {
	echo "$*" | sed "s/'/\\\'/g"
}

if [ -z "$MYSQL_OPTS" ]
then
    MYSQL_OPTS="";
fi

if [ -n "$MYSQL_USER" ]
then
    MYSQL_OPTS="-u$MYSQL_USER $MYSQL_OPTS"
fi

if [ -n "$MYSQL_PORT_3306_TCP_ADDR" ]
then
	MYSQL_HOST_OPTS="-h$MYSQL_PORT_3306_TCP_ADDR"

	if [ $MYSQL_PORT_3306_TCP_PORT -ne 3306 ]
	then
		echo "MySQL Port: $MYSQL_PORT_3306_TCP_PORT"
		MYSQL_HOST_OPTS="$MYSQL_HOST_OPTS -P$MYSQL_PORT_3306_TCP_PORT"
	fi
	
	MYSQL_OPTS="$MYSQL_HOST_OPTS $MYSQL_OPTS"
fi

MYSQL="mysql $MYSQL_OPTS"
