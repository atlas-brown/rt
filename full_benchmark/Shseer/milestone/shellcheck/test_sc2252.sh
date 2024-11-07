#!/bin/sh
test -f "$1"
if [ -f "$1" ] ; then 
echo "always true"
fi