#!/bin/sh

#Variable change in subshell
count=0
f () {
    count=$((count+=1))
    python3 run.py
}
echo "Output is $(f)"