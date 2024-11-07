#!/bin/sh

if [ -f /opt/mysql-bootstrap/common.sh ]
then
    . /opt/mysql-bootstrap/common.sh
else
    echo "Error: /opt/mysql-bootstrap/common.sh does not exist"
    exit 1
fi

if [ -z "$DATABASE" ]
then
	echo "Error: Database name not provided"
	exit 3
fi

mysql_cmd="$MYSQL --disable-column-names"
database_count_query="SET @db = '"`add_slashes_sq $DATABASE`"'; \
SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = @db"
database_count=`$mysql_cmd -e "$database_count_query"`

if [ ! $? -eq 0 ]
then
	echo " > Error: MySQL Command Failed"
	echo " >> Command: $mysql_cmd"
	echo " >> Query: $database_count_query"
	exit 2
fi

should_create_database=1

if [ $database_count -gt 0 ]
then
	echo " > Database already exists"
	if [ -n "$DATABASE_DROP" ] && [ $DATABASE_DROP -eq 1 ]
	then
		echo " >> Dropping Database"
		drop_user_query="DROP DATABASE $DATABASE"
		$mysql_cmd -e "$drop_user_query"

		if [ ! $? -eq 0 ]
		then
			echo "Error: MySQL Command Failed"
			echo " >> Command: $mysql_cmd"
			echo " >> Query: $drop_user_query"
			exit 2
		fi
	else
		should_create_database=0
		echo " >> Skipping Database Commands"
	fi
fi

if [ $should_create_database -eq 1 ]
then
	echo " > Creating Database"
	drop_user_query="CREATE DATABASE $DATABASE"
	$mysql_cmd -e "$drop_user_query"

	if [ ! $? -eq 0 ]
	then
		echo "Error: MySQL Command Failed"
		echo " >> Command: $mysql_cmd"
		echo " >> Query: $drop_user_query"
		exit 2
	fi

	/opt/mysql-bootstrap/bootstrap-database.sh
fi

