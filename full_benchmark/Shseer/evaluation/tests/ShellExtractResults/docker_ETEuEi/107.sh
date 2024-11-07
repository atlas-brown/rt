#!/bin/sh

. /opt/mysql-bootstrap/common.sh

$MYSQL -e "SELECT VERSION()" > /dev/null

if [ ! $? -eq 0 ]
then
    echo "Error: Could not connect to database"
    exit 3
fi

if [ -z "$DATABASE" ]
then
    echo "Error: Database name not provided"
    exit 3
fi

/opt/mysql-bootstrap/create-database.sh

if [ -n "$DATABASE_USER" ]
then
    /opt/mysql-bootstrap/create-user.sh
fi
