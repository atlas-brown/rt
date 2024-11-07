#!/bin/bash

/bin/echo "Put your record start code here" >> /tmp/videosave_start
/usr/bin/sudo /usr/sbin/service videosave start >> /tmp/videosave_start &

