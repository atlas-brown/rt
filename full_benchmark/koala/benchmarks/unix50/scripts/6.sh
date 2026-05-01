#!/bin/bash

# 3.1: get lowercase first letter of last names (awk)
# @file "$1": "BBCD ABCD\nQWER WERT03214\nLKJHGF KJHGFD\n"
# @output "awk"
cat $1 | cut -d ' ' -f 2 | cut -c 1-1 | tr -d '\n' | tr '[A-Z]' '[a-z]'
