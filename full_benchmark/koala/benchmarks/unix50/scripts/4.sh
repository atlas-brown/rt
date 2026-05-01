#!/bin/bash

# 1.3: sort top first names
# @concretize "$1" --> "../fixtures/1.txt"
# @expect "[A-Z][a-z]+" --> "sort"
# @expect "( )*[0-9]+ +[A-Z][a-z]+" --> "sort -r"
cat $1 | cut -d ' ' -f 1 | sort | uniq -c | sort -r
