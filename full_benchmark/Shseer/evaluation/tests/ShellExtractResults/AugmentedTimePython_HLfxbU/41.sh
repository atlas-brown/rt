#!/bin/bash

while read name
do
    if [ $(echo "$name -ne 0" | bc -l ) ]
    then
        icount=$((icount +1))
        sum=$(echo $sum+$name | bc )
    fi
done < 54.187.130.169.events.log
