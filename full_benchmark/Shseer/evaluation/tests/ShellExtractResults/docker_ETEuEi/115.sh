#!/bin/sh

. /opt/mysql-bootstrap/common.sh

mysql_cmd="$MYSQL --disable-column-names"

database_count_query="SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'bstest2'"
database_count=`$mysql_cmd -e "$database_count_query"`

if [ $database_count -eq 1 ]
then
    exit 0
else
    exit 255
fi
