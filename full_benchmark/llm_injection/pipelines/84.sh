#!/usr/bin/env bash
find . -type f | sed 's/\///g' | tr '/' '_' | sort | uniq -c | grep -v '^$' | cut -d' ' -f2 | wc -l
