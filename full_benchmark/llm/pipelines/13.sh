#!/usr/bin/env bash
# @assume "ls" --> ".*"
ls | grep ".txt" | cut -d' ' -f5 | sort -n | uniq | xargs -I {} find . -name "{}" | tr 'a-z' 'A-Z' | wc -l
