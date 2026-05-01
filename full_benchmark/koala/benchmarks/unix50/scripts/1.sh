#!/bin/bash

# 1.0: extract the last name
# @file "$1": "[A-Za-z-']+ [A-Za-z-']+"
cat $1 | cut -d ' ' -f 2
