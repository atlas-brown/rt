#!/bin/bash

# 1.2: extract names and sort
grep -Eo [0-9]+ $1 | sort -n
cat $1 | head -n 2 | cut -d ' ' -f 2
