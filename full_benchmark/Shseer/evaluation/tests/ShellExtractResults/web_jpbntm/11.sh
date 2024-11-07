#!/bin/bash
if (( $# < 2 ))
then
    echo "[ERROR] Please supply output RTMP UTR and file location"
    echo -e "$0 <RTMP URL> <Output File>"
    exit 2
fi
src="rtmpsrc location=$1"
gst-launch-1.0 ${src} ! filesink location="$2"
