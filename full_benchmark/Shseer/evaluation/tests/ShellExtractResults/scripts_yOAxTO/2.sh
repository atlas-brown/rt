#!/bin/bash
PROCESS=$1
#number=$(ps aux | grep $PROCESS | wc -l)

number=$(ps xc | grep "$PROCESS" | wc -l)
result_check="Running"
if [ $number -gt 0 ]
    then
        echo "Running";
fi