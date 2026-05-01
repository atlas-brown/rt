#!/usr/bin/env bash
find . -type f | sed 's/[0-9]//g' | grep '[0-9]' | sort | uniq -c | tr -s ' ' | cut -d' ' -f2 | wc -l
