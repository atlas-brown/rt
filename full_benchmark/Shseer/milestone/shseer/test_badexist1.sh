#!/bin/sh
case $1 in
 upgrade) 
    rm -r bin
    rm logs.txt
    ;;
esac
#deleting logs.txt twice if 1=logs.txt
rm logs.txt