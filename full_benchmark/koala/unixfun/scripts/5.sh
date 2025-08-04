#!/bin/bash

# 2.1: get all Unix utilities
# @file "$1": "[A-Z]+ is a [a-z,]+, (and|\\.)"
# @output "[a-z]*"
cat $1 | cut -d ' ' -f 4 | tr -d ','
