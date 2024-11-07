#!/bin/sh

. /opt/mysql-bootstrap/common.sh

mysql_cmd="$MYSQL --disable-column-names"

table_count_query="SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'bstest1' AND table_name = 'test_sql'"
table_count=`$mysql_cmd -e "$table_count_query"`

if [ $table_count -eq 1 ]
then
    exit 0
else
    exit 255
fi
