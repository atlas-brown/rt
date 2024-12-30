#!/bin/bash

# 5.1: extract hello world
# @assume "grep 'print'" --> "printf(\"hello, world\n\");"
# @output "hello, world"
cat $1 | grep 'print' | cut -d "\"" -f 2 | cut -c 1-12
