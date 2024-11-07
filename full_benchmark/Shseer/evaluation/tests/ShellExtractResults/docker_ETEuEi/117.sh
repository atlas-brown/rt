#!/bin/sh

. /opt/mysql-bootstrap/common.sh

DATABASE_HOST="172.16.0.0/255.240.0.0"

mysql_cmd="$MYSQL --disable-column-names"

grant_count_query="SET @user = '"`add_slashes_sq $DATABASE_USER`"', \
@host = '"`add_slashes_sq $DATABASE_HOST`"', \
@database = '"`add_slashes_sq $DATABASE`"'; \
SELECT COUNT(*) FROM mysql.db WHERE user = @user AND host = @host AND db = @database" 
grant_count=`$mysql_cmd -e "$grant_count_query"`

if [ $grant_count -eq 1 ]
then
    exit 0
else
    exit 255
fi
