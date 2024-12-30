#!/bin/bash

# 6.1: order the bodies by how easy it would be to land on them in Thompson's Space Travel game when playing at the highest simulation scale
# @assume "cat ${1}" --> "[A-Z][a-z]+ [0-9.]+"
# @assume "awk \"{print \$2, \$0}\"" --> "[0-9.]+ [A-Z][a-z]+ [0-9.]+"
cat $1 | awk "{print \$2, \$0}" | sort -nr | cut -d ' ' -f 2
