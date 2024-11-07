#!/bin/sh

case $1 in 
    *.sh )
    true 
    ;;
    *)
    exit 0
    ;;
esac
#This comparison can never be true
if [ "$1" = "foo" ] ; then
echo "yes"
fi 