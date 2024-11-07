#!/bin/sh
#desc:Developer manual
#package:oddevel

# Copyright(c) 2015 OpenDomo Services SL. Licensed under GPL v3 or later

## This service will display the manual page corresponding to the requested service.

echo "#>Developer manual"
if test -z "$1"; then
	echo "list:developerManual.sh	detailed filterable"
	echo "#LOADING Loading ..."
	cd /usr/local/opendomo/
	for filename in *.sh; do
		name=`echo $filename | cut -f1 -d.`
		desc=`head -n5 $filename | grep '#desc' | cut -f2- -d:`
		echo "	-$name	$name 	chapter	$desc"
	done
	echo "	-intro	Introduction	chapter"
else
	echo "list:developerManual.sh"
	if grep -q '^##' /usr/local/opendomo/$1.sh; then
		grep '^##' /usr/local/opendomo/$1.sh | sed 's/##/# /'
		#':a;N;$!ba;s/\n/ /g'
	else
		echo "#WARN This file is not documented"
	fi
	echo "actions:"
	echo "	goback	Back"
fi
echo
