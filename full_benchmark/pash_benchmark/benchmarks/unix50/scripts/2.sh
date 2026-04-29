#!/bin/bash

# 1.1: extract names and sort
# @concretize "$1" --> "../fixtures/1.txt"
# @output "(Ritchie|Thompson)"
cat $1 | cut -d ' ' -f 2 | sort
