#!/bin/bash

# @assume "cat $1" --> ".*\t.*"
# stream enable
#cat $1 | cut -f 2

# @assume "cat $1" --> ".*\t.*"
# stream enable
cat $1 | cut -f 3
