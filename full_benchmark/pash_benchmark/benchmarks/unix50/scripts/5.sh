#!/bin/bash

# 2.1: get all Unix utilities
# @assume "cat $1" --> "[A-Z] is[A-Za-z,](, and|\\.)"
# @output "[a-z]+"
cat $1 | cut -d ' ' -f 4 | tr -d ','
