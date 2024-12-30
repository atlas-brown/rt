#!/bin/bash

# 3.1: get lowercase first letter of last names (awk)
# @assume "cat $1" --> "[A-Za-z]+ [A-Za-z]+"
# @output "awk"
cat $1 | cut -d ' ' -f 2 | cut -c 1-1 | tr -d '\n' | tr '[A-Z]' '[a-z]'
