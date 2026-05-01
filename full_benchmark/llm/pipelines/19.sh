#!/usr/bin/env bash
cat file.txt | tr ' ' '\n' | cut -f2 | sort -u | uniq -c | tr -s ' ' | cut -d' ' -f2 | sort -n
