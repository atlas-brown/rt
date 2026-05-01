#!/usr/bin/env bash
find . -type f | xargs wc -l | tr -s ' ' | tr ' ' '\t' | tr -d ' ' | cut -f1 | sort -n | uniq -c
