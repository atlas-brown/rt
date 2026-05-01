#!/usr/bin/env bash
# @file "data.txt": "[0-9a-zA-Z]+"
cat data.txt | tr -d '[:punct:]' | grep "[0-9]" | sort | sed 's/[0-9]/#/g' | uniq -c | wc -l
