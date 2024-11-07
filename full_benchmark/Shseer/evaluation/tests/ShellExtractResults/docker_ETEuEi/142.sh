#!/bin/sh

# If cnonfigured, ensure the UID of the mysql directory is correct
if [ -n "$SYNC_UID" -a "$SYNC_UID" = "1" ]
then
	if [ -d /var/lib/mysql ]
	then
	    uid=`stat -c '%u' /var/lib/mysql`
	    gid=`stat -c '%g' /var/lib/mysql`

	    echo "Updating mysql ids to ($uid:$gid)"

	    # Only update the ids if they're not root
	    if [ ! $uid -eq 0 ]
	    then
		sed -i "s#^mysql:x:.*:.*:#mysql:x:$uid:$gid:#" /etc/passwd
	    fi

	    if [ ! $gid -eq 0 ]
	    then
		sed -i "s#^mysql:x:.*:#mysql:x:$gid:#" /etc/group
	    fi

	    chown mysql:mysql /var/run/mysqld
	fi
fi

INIT_MYSQL=0
if [ ! -d /var/lib/mysql/mysql ]
then
     mysql_install_db --user=mysql > /dev/null
     INIT_MYSQL=1
fi

MYSQL_OPTS="--skip-syslog $MYSQL_OPTS"

if [ $INIT_MYSQL -eq 1 ]
then
    if [ -z "$ADMIN_USER" ]
    then
        ADMIN_USER="admin"
    fi

    if [ -z "$ADMIN_HOST" ]
    then
        ADMIN_HOST="172.16.0.0/255.240.0.0"
        echo "Allowing connections to user '$ADMIN_USER' from $ADMIN_HOST"
    fi

    if [ -z "$ADMIN_PASS" ]
    then
        ADMIN_PASS=$(pwgen -s 12 1)
        echo "Generated password for user '$ADMIN_USER': $ADMIN_PASS"
    fi

    touch /tmp/mysql-init.sql
    chown mysql /tmp/mysql-init.sql
    chmod 700 /tmp/mysql-init.sql

    echo "DELETE FROM mysql.user WHERE user != 'root' ;" >> /tmp/mysql-init.sql
    echo "GRANT ALL ON *.* TO '$ADMIN_USER'@'$ADMIN_HOST' IDENTIFIED BY '$ADMIN_PASS' WITH GRANT OPTION;" > /tmp/mysql-init.sql
    echo "DROP DATABASE IF EXISTS test;" >> /tmp/mysql-init.sql
    echo "FLUSH PRIVILEGES;" >> /tmp/mysql-init.sql

    # When done, output to a file so we know we can delete the init file
    echo "SELECT 'Done' INTO OUTFILE '/tmp/mysql-init-done'" >> /tmp/mysql-init.sql

    MYSQL_OPTS=" --init-file=/tmp/mysql-init.sql $MYSQL_OPTS"
fi

exec /usr/bin/mysqld_safe $MYSQL_OPTS &

# Remove the temporary file when initializtion is complete
if [ -f /tmp/mysql-init.sql ]
then
    while [ ! -f /tmp/mysql-init-done ]
    do
        sleep 1
    done
    rm /tmp/mysql-init.sql /tmp/mysql-init-done
fi
wait
