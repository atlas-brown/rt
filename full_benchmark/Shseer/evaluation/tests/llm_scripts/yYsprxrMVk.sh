#!/bin/sh

if [ -d $1 ] ; then
    tar -czvf $2.tar.gz $1
fi
