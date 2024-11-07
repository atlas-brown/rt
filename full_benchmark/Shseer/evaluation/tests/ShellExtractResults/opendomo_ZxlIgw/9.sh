#!/bin/sh
#desc:Configure Github account
#type:local
#package:oddevel

# Copyright(c) 2015 OpenDomo Services SL. Licensed under GPL v3 or later

CONFIGFILE="/home/$USER/.gitdata"

if ! test -z "$2"; then
	echo "USERNAME=$1" > $CONFIGFILE
	echo "PASSWORD=$2" >> $CONFIGFILE
fi

source $CONFIGFILE

echo "#> User account in Github"
echo "form:configureGithub.sh"
echo "	username	Username	text	$USERNAME"
echo "	password	Password  	text	$PASSWORD"
echo 
