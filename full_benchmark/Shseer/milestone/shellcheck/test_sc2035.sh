#!/bin/sh

if [ $# -ne 2 ]; then
    exit 0
fi

case $1 in
    "-r")
    #Using $1 instead of $2 caused $1 to be interpted as option
    rm -f "$1" #This becomes rm -f -r
    ;;
    *)
    exit 0
    ;;
esac