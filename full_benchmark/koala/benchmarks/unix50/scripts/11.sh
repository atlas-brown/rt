#!/bin/bash

# 4.5: 4.4 + pawns
# @concretize "$1" --> "../fixtures/chess-captures.txt"
# @output " *[0-9]+ (N|P|Q)"
cat $1 | tr ' ' '\n' | grep 'x' | grep '\.' | cut -d '.' -f 2 | cut -c 1-1 | tr '[a-z]' 'P' | sort | uniq -c | sort -nr
