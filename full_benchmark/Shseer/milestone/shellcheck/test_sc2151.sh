#!/bin/sh

f () {
    output=$(python3 run.py)
    #Output may be a string
    return "$output"
}
f