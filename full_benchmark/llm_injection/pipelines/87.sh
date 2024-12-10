#!/usr/bin/env bash
find . -type f | sort -u | uniq -c | sort -nr | grep -v '^$' | tr -s ' ' | cut -d' ' -f2 | wc -l
