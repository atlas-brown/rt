#!/bin/bash

rm -rf chunked/
mkdir chunked

count=0
counter=0
files=$(ls original/*xml)
for i in $files; do
    cat $i >> chunked/chunk$counter.xml
    let counter=counter+1
    if [ $counter -gt 100 ]; then
        let count=count+1
        let counter=0
    fi
done
