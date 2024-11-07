#!/bin/sh

bootstrap_cat() {
	for file in $*
	do
		case $file in
		     *.bz2)   bzcat "$file" ;;
		     *.gz)    zcat "$file"  ;;
		     *.xz)    xzcat "$file" ;;
		     *)       cat "$file"   ;;
		esac
	done
}

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

if [ $database_count -eq 0 ]
then
	echo " > Database does not exist: Skiping Bootstrap"
	exit 2;
fi

if [ -n "$DATABASE_BOOTSTRAP" ]
then
	$DATABASE_BOOTSTRAP
else
	if [ -n "$DATABASE_SQL" ]
	then
		if [ -f "$DATABASE_SQL" ]
		then
			bootstrap_cat $DATABASE_SQL | $MYSQL $DATABASE
		else
			if [ -d "$DATABASE_SQL" ]
			then
			    bootstrap_cat $DATABASE_SQL/* | $MYSQL $DATABASE
			else
				echo "Error: SQL File does not exist ($DATABASE_SQL)"
			fi
		fi
	fi
fi
