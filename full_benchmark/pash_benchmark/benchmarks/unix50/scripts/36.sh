#!/bin/bash

# 11.2: most repeated first name in the list?
# @assume "cat $1" --> "[0-9]{4}\t[A-Zand\\. ]+\t.+"
# @output "\t[A-Z]+"
# @expect "[A-Z]+" --> "sort"
cat $1 | cut -f 2 | cut -d ' ' -f 1 | sort | uniq -c | sort -nr | head -n 1 | fmt -w1 | sed 1d
