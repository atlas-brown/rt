#!/bin/sh
#desc:Update system
#type:local
#package:oddevel

# Copyright(c) 2015 OpenDomo Services SL. Licensed under GPL v3 or later

ODAPTPID=/var/opendomo/run/opendomo-apt.pid

echo "list:updateSystem.sh"
if grep Spaceless $ODAPTPID &>/dev/null 
then
	echo "#WARN No free space available, you need to save configuration and reboot to continue"
	echo "actions:"
	echo "	saveConfig.sh	Save configuration"
else
	echo "#INFO Updating system. Please wait"
	echo "" > /var/opendomo/apt/queue
	echo 0 > /var/opendomo/apt/update
fi
echo
