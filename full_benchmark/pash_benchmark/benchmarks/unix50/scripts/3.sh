#!/bin/bash

# 1.2: extract names and sort
# @concretize "$1" --> "../fixtures/1.txt"
# @output "[A-Za-z-']+"
cat $1 | head -n 2 | cut -d ' ' -f 2
