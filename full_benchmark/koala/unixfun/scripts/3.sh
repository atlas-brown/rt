#!/bin/bash

# 1.2: extract names and sort
# @file "$1": "[A-Za-z-']+ [A-Za-z-']+"
# @output "[A-Za-z-']+"
cat $1 | head -n 2 | cut -d ' ' -f 2
