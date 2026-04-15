#!/bin/bash

# 8.1: count unix birth-year
# @output " *[0-9]+"
cat $1 | tr ' ' '\n' | grep 1969 | wc -l
