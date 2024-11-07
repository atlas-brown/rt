#!/bin/sh
#Variable count is unused
count=0
i=5
while [ $i -lt 5 ] ; do
    echo "Count is $count"
    count=$((count + 1))
done 
#Loop will never run and and hence count is never used
# This is a bit contrived