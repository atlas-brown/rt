#!/bin/bash

# 1.1: extract names and sort
# @file "$1": "[A-Za-z-']+ [A-Za-z-']+"
# @output "(?!(.* .*))"
cat $1 | cut -d ' ' -f 2 | sort
