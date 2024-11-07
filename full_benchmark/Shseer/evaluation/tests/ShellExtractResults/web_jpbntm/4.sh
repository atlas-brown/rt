#!/bin/bash
for slidehost in $(cat ../system-configs/computer_list.txt ) ; do
	#echo "Supposedly waking $xx"
	ssh ubuntu@$slidehost "export DISPLAY=:1 ; xset -dpms ; xset s off ; xset s noblank"
done
