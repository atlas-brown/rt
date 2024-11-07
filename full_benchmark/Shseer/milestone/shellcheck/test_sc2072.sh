#!/bin/sh
x="3.12"
#can't compare decimals
if [ 0 -lt $x ]; then 
    echo "wut"
fi