#!/bin/sh

# Quick function to help escape values going into the icinga config
sed_escape() {
        echo "$*" | sed 's/"/\\\\"/g' | sed 's/#/\\#/g'
}

if [ -z "$DB_NAME" ]
then
    DB_NAME="icinga"
fi

if [ -z "$DB_USER" ]
then
    DB_USER="icinga"
fi

if [ -z "$DB_PASS" ]
then
    DB_PASS=""
fi

if [ -z "$DB_HOST" ]
then
    if [ -z "$MYSQL_PORT_3306_TCP_ADDR" ]
    then
        DB_HOST="$MYSQL_PORT_3306_TCP_ADDR"
    elif [ -z "$DB_PORT_3306_TCP_ADDR" ]
    then
	DB_HOST="$DB_PORT_3306_TCP_ADDR"
    else
        # Default to localhost (you can share a mysql socket instead)
        DB_HOST="localhost"
    fi
fi

# Update the configuration file with the new values
sed_name=`sed_escape "$DB_NAME"`
sed_host=`sed_escape "$DB_HOST"`
sed_user=`sed_escape "$DB_USER"`
sed_pass=`sed_escape "$DB_PASS"`

sed -i 's#database = ".*",$#database = "'"$sed_name"'"#g' /etc/icinga2/features-available/ido-mysql.conf
sed -i 's#user = ".*",$#user = "'"$sed_user"'",#g' /etc/icinga2/features-available/ido-mysql.conf
sed -i 's#password = ".*",$#password = "'"$sed_pass"'",#g' /etc/icinga2/features-available/ido-mysql.conf
sed -i 's#host = ".*",$#host = "'"$sed_host"'",#g' /etc/icinga2/features-available/ido-mysql.conf
