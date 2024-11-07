#!/bin/sh

case $1 in
    remove)
        rm $2
        ;;
    rename)
        mv $2 $3
        ;;
    append)
        cat $2 >> $3
        ;;
    overwrite)
        cat $2 > $3
        ;;
esac