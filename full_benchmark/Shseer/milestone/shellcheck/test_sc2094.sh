#!/bin/sh
if [ "$1" = "foo.txt" ] ; then 
    grep foo "$1" | sed -e 's/foo/bar/g' > "foo.txt"
fi
