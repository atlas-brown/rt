#!/bin/sh

. /opt/mysql-bootstrap/common.sh

DATABASE_HOST="172.16.0.0/255.240.0.0"

mysql_cmd="$MYSQL --disable-column-names"

user_count_query="SET @user = '"`add_slashes_sq $DATABASE_USER`"', \
@host = '"`add_slashes_sq $DATABASE_HOST`"'; \
SELECT COUNT(*) FROM mysql.user WHERE user = @user AND host = @host" 
user_count=`$mysql_cmd -e "$user_count_query"`

if [ $user_count -eq 1 ]
then
    exit 0
else
    exit 255
fi
