#!/bin/bash

# 8.3: find names of the four people most involved with unix
# @file "$1": "[A-Za-z,\\. ]+ (\([A-Za-z,\\. ]+\) )*"
# @output "[A-Za-z,\\. ]+"
cat $1 | grep '(' | cut -d '(' -f 2 | cut -d ')' -f 1 | head -n 1
