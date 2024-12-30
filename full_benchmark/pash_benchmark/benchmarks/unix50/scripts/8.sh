#!/bin/bash

# 4.2: find pieces captured by Belle
# @output "[0-9]+"
cat $1 | tr ' ' '\n' | grep 'x' | grep '\.' | wc -l
