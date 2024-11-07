#!/bin/sh

count=010
i=0
#Comparing numbers using string op
while [ $i != $count ] ; do
    echo "$i"
    i=$((i+1))
done 