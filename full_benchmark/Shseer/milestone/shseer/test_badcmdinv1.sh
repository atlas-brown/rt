#!/bin/sh

if [ -d "$1/build" ] ; then
    # need -r to delete directory
    rm "$1"/build
fi
