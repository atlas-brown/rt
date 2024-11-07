#!/bin/sh

if [ -f /opt/mysql-bootstrap/common.sh ]
then
    . /opt/mysql-bootstrap/common.sh
else
    echo "Error: /opt/mysql-bootstrap/common.sh does not exist"
    exit 1
fi

if [ -z "$DATABASE_HOST" ]
then
	echo " > Host not provided: using default host (172.16.0.0/255.240.0.0)"
	DATABASE_HOST="172.16.0.0/255.240.0.0"
fi

if [ -z "$DATABASE_GRANT" ]
then
	echo " > Privileges not specified; using default privileges (ALL)"
	DATABASE_GRANT="ALL"
fi

mysql_cmd="$MYSQL --disable-column-names"
user_count_query="SET @user = '"`add_slashes_sq $DATABASE_USER`"'; \
SELECT COUNT(*) FROM mysql.user WHERE user = @user" 
user_count=`$mysql_cmd -e "$user_count_query"`

if [ ! $? -eq 0 ]
then
	echo " > Error: MySQL Command Failed"
	echo " >> Command: $mysql_cmd"
	echo " >> Query: $user_count_query"
	exit 2
fi

should_create_user=1

if [ $user_count -gt 0 ]
then
	echo " > User already exists"
	if [ -n "$USER_DROP" ] && [ $USER_DROP -eq 1 ]
	then
		echo " >> Dropping User"
		drop_user_query="SET @user = '"`add_slashes_sq $DATABASE_USER`"'; \
DELETE FROM mysql.user WHERE user = @user; \
DELETE FROM mysql.db WHERE user = @user" 
		$mysql_cmd -e "$drop_user_query"

		if [ ! $? -eq 0 ]
		then
			echo "Error: MySQL Command Failed"
			echo " >> Command: $mysql_cmd"
			echo " >> Query: $drop_user_query"
			exit 2
		fi
	else
		should_create_user=0
		host_count_query="SET @user = '"`add_slashes_sq $DATABASE_USER`"', \
@host = '"`add_slashes_sq $DATABASE_HOST`"'; \
SELECT COUNT(*) FROM mysql.user WHERE user = @user AND host = @host" 
	
		host_count=`$mysql_cmd -e "$host_count_query"`

		if [ ! $? -eq 0 ]
		then
			echo "Error: MySQL Command Failed"
			echo " >> Command: $mysql_cmd"
			echo " >> Query: $host_count_query"
			exit 2
		fi

		if [ $host_count -eq 0 ]
		then
			echo " >> User is not authorized from $DATABASE_HOST"
		else
			echo " >> User is already authorized from $DATABASE_HOST"
		fi
	fi
fi

if [ $should_create_user -eq 1 ]
then
	echo " > User '$DATABASE_USER' does not exist"
	
	if [ -z "$DATABASE_PASS" ]
	then
		if [ "$DATABASE_PASS_EMPTY" != "1" ]
		then
			echo ' > Password not provided: Generating One'
			DATABASE_PASS=`pwgen -s 12 1`
		fi
	fi

	privileges_query="SELECT column_name FROM information_schema.columns \
WHERE table_schema = 'mysql'\
  AND table_name = 'db'\
  AND column_name LIKE '%_priv'
  AND column_name != 'Grant_priv'"
	privileges=`$mysql_cmd -e "$privileges_query"`
	if [ ! $? -eq 0 ]
	then
		echo "Error: MySQL Command Failed"
		echo " >> Command: $mysql_cmd"
		echo " >> Query: $privileges_query"
		exit 2
	fi

	priv_columns=""
	priv_values=""
	for priv in $privileges
	do
		priv_columns="$priv_columns, ${priv}"
		priv_values="$priv_values, \"y\""
	done

	create_user_query="SET @user = '"`add_slashes_sq $DATABASE_USER`"',\
@password = '"`add_slashes_sq $DATABASE_PASS`"',\
@host = '"`add_slashes_sq $DATABASE_HOST`"',\
@db = '"`add_slashes_sq $DATABASE`"';\
INSERT INTO mysql.user (user, host, password) VALUES (@user, @host, PASSWORD(@password));\
INSERT INTO mysql.db (user, host, db$priv_columns) VALUES (@user, @host, @db$priv_values);
FLUSH PRIVILEGES;"
	$mysql_cmd -e "$create_user_query"

fi

