#!/bin/sh
# https://stackoverflow.com/questions/49658154/how-sed-command-used-in-shell-script

# input:
# dummy statement Hello world 
# dummy 1 statement Hello Mike

file=commit.txt
while IFS= read line; do
    # bug 1: sed is not receiving input
    # bug 2: sed regex does not match expected input

    # @expect "sed "s/  HELLO.*'[^']*'/ /"" --> "dummy statement Hello world\ndummy 1 statement Hello Mike"
    # @expect "sed "s/  HELLO.*'[^']*'/ /"" --> ".*Hello.*"
    # @expect "sed "s/  HELLO.*'[^']*'/ /"" --> ".+"
    commitid=$line | sed "s/  HELLO.*'[^']*'/ /"
    echo $commitid # Returning null
done < "$file"
