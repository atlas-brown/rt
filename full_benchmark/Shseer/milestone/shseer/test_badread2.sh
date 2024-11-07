#!/bin/sh

if [ "$2" = "$1" ] ; then
    rm "$2"
    #will fail as $1=$2
    rm "$1"
fi