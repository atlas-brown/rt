#!/bin/bash

# 1.0: extract the last name
# @assume "cat $1" --> "[A-Za-z-']+ [A-Za-z-']+"
cat $1 | cut -d ' ' -f 2
