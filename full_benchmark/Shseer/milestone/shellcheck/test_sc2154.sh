#!/bin/sh

if [ $# -ne 1 ];then
exit 1
fi

shift
#1 is ""
echo "1 is $1"