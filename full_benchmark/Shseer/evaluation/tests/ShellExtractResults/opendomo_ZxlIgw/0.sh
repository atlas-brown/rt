#!/bin/sh
### BEGIN INIT INFO
# Provides:          oddevel
# Required-Start:    
# Required-Stop:
# Should-Start:      
# Default-Start:     1 2 3 4 5
# Default-Stop:      0 6
# Short-Description: Simulator
# Description:       Simulate several hardware devices
#
### END INIT INFO
### Copyright(c) 2015 OpenDomo Services SL. Licensed under GPL v3 or later

. /lib/lsb/init-functions
PIDFILE="/var/opendomo/run/simulator.pid"

do_background() {
	# 1. Saving PID file
	echo -n >$PIDFILE

	# 2. Performing the actual loop
	while test -f $PIDFILE
	do
		sleep 5
	done
}
	
do_start () {
	log_action_begin_msg "Starting simulator"
	if ! test -f $PIDFILE; then
		# 0. Pre-required directories
		test -d /etc/opendomo/control || mkdir -p /etc/opendomo/control
		test -d /etc/opendomo/vision || mkdir -p /etc/opendomo/vision
		
		# 1. Simulate a ODEnergy device:
		echo 'URL="http://127.0.0.1/"
TYPE="odenergy"
REFRESH=10
USERNAME=""
PASS=""
DEVNAME="odenergydemo"' > /etc/opendomo/control/odenergydemo.conf
		
		# 2. Simulate a ODControl device:
		echo 'URL="http://127.0.0.1/cgi-bin/odcontrol2.cgi/"
TYPE="odcontrol2"
REFRESH=10
USERNAME=""
PASS=""
DEVNAME="odcontroldemo"' > /etc/opendomo/control/odcontroldemo.conf	
	
	
		# 3. Simulate a IP camera
		echo 'URL=http://127.0.0.1/cgi-bin
TYPE="foscam"
REFRESH=1
USERNAME=""
PASS=""
DEVNAME="foscamdemo"' > /etc/opendomo/control/foscamdemo.conf	
		
		echo 'NAME=foscamdemo
TYPE=ip
DESCRIPTION="Simulated camera"' > /etc/opendomo/vision/foscamdemo.conf	

		cd /usr/local/opendomo/daemons/
		$0 background > /dev/null &
	fi
	log_action_end_msg $?
}

do_stop () {
	log_action_begin_msg "Stoping simulator"
	rm $PIDFILE 2>/dev/null	
	# 1. Delete odenergy simulated device:
	rm -fr /etc/opendomo/control/odenergydemo*
	# 2. Delete odcontrol2 simulated device:
	rm -fr /etc/opendomo/control/odcontroldemo*
	# 3. Delete simulated camera
	rm -fr /etc/opendomo/control/foscamdemo*
	rm -fr /etc/opendomo/vision/foscamdemo.conf	
	
	log_action_end_msg $?
}

do_status () {
	if test -f $PIDFILE; then
		echo "simulator is running"
		exit 0
	else
		echo "simulator is not running"
		exit 1
	fi
}

case "$1" in
	background)
		do_background
		;;
	start)
		do_start
		;;
	restart|reload|force-reload)
		do_stop
		do_start
		exit 3
		;;
	stop)
		do_stop
		exit 3
	;;
	status)
		do_status
		exit $?
		;;
	*)
		echo "Usage: $0 [start|stop|restart|status]" >&2
		exit 3
		;;
esac