#!/bin/bash

# 2.1: get all Unix utilities
# @concretize "$1" --> "../fixtures/5.txt"
# @output "[a-z]*"
cat $1 | cut -d ' ' -f 4 | tr -d ','
