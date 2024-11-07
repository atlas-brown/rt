#!/bin/bash

export result1="1.0" 
export result2="2.0"

if [ $(echo "$result1 < $result2" | bc -l ) ]; then
    echo "yes"
    else
        echo "no" 
fi
