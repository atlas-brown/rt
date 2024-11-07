#!/usr/bin/bash

. /lib/svc/share/smf_include.sh
. /lib/sdc/config.sh

load_sdc_sysinfo
load_sdc_config

#state_dir=/var/db/nut
state_dir=/opt/nut/var/state
driver_pid=`ps -ef | grep [b]lazer_usb | awk '{ print $2 }'`
upsd_pid=`ps -ef | grep [u]psd | awk '{ print $2 }'`
upsmon_pid=`ps -ef | grep [u]psmon | awk '{ print $2 }'`

case "$1" in
	start)
		/usr/bin/rm -rf ${state_dir}/*
  		/opt/nut/bin/blazer_usb -a mustek > /dev/null 2>&1 &
		sleep 3
		/opt/nut/sbin/upsd -u nut > /dev/null 2>&1 &
                sleep 2
		/opt/nut/sbin/upsmon > /dev/null 2>&1 &
		;;
	stop)
		for pid in ${upsmon_pid}
		do
		    /usr/bin/kill -9 ${pid}
		done
	        /usr/bin/kill -9 ${upsd_pid}
		/usr/bin/kill -9 ${driver_pid}
		/usr/bin/rm -rf ${state_dir}/*
		;;
	\*)
		echo ""
		echo "Usage: `basename $0` { start | stop }"
		echo ""
		exit 64
		;;
esac

exit $SMF_EXIT_OK
