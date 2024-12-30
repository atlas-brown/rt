#!/bin/bash

# 1.1: extract names and sort
# @assume "cat $1" --> "[A-Za-z-']+ [A-Za-z-']+"
# @output "(?!(.* .*))"
cat $1 | cut -d ' ' -f 2 | sort
