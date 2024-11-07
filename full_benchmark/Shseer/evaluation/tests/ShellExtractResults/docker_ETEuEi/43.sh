#!/bin/sh -x
if [ -f /opt/icinga2/configure-ido-mysql.sh ]
then
	/opt/icinga2/configure-ido-mysql.sh
fi

exec /opt/init-icinga2.sh
