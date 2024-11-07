#!/bin/bash

# This script should be called with the complete URL of the stream source
if (( $# != 1 ))
then
    echo "Error:  invalid number of arguments provided"
    exit 1
fi
export DISPLAY=:1
# Abort if the DISPLAY variable is not properly set
if [[ "$DISPLAY" == "" ]]
then
    echo "Error:  DISPLAY not defined"
    exit 2
fi
WIDTH="$(xrandr | sed -n 's/.*current \([0-9]*\) x \([0-9]*\).*/\1/p')"
HEIGHT="$(xrandr | sed -n 's/.*current \([0-9]*\) x \([0-9]*\).*/\2/p')"
{
    while (( 1 ))
    do
        gst-launch-1.0 playbin uri="$1" & 
        echo $! > /tmp/vlc-scale.pid
        wait
        ret="$?"
        if [[ "$ret" == "0" ]]
        then
             exit
        fi
        curl=`curl -f -s -I $1 2> /dev/null`
        retval=$?
        while [ $retval -ne 0 ]; do
            curl=`curl -f -s -I $1 2> /dev/null`
            retval=$?
        done       
    done
} < /dev/null 1> /dev/null 2> /dev/null &
