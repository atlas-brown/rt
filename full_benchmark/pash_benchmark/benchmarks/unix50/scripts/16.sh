#!/bin/bash

# 7.2: find  most frequently occurring machine
# @assume "cat $1" --> "[a-zA-Z0-9]+ [a-zA-Z0-9]+"
# @output "[a-zA-Z0-9]+"
cat $1 | cut -f 2 | sort -n | uniq -c | sort -nr | head -n 1 | tr -s ' ' '\n' | tail -n 1
