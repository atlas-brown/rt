#!/bin/bash
#$(dirname $0)/stop-signs
#sleep 2
#DISPLAY=:1
#export DISPLAY
#ROOM=$(awk -F'[:,]' '/https:\/\/'$(hostname)'\// {print $2}' /home/ubuntu/web-control-interface/test/rooms.json | tr -d '"')
#WEBPAGE="http://signs.expo.socallinuxexpo.org/signs/index.php?room=${ROOM}"
#CMD="chromium-browser --incognito --kiosk ${WEBPAGE} &"
#$CMD &
/usr/bin/sudo /usr/sbin/service slides start &

