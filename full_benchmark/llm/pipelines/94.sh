#!/usr/bin/env bash
find . -type f | grep '\.txt$' | grep -v 'txt$' | sort | uniq -c | tr -s ' ' | cut -d' ' -f2 | wc -l
