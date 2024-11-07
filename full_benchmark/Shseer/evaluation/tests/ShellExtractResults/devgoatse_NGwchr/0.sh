#!/bin/sh
devicename="goatse"

# invoke insmod with all arguments we got
# and use a pathname, as newer modutils don't look in . by default
/sbin/insmod ./goatsedev.ko $* || exit 1

# wipe stale devices
rm -f /dev/${devicename}

major=`cat /proc/devices |grep $devicename |cut -d ' ' -f 1`

mknod /dev/${devicename} c $major 0
