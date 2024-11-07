#!/bin/sh

output="output.txt"
for file in /path/to/directory/*
do
    if [ ${file: -4} != ".pdf" ]; then
        cat $file >> $output
    fi
done
