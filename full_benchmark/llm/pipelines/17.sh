#!/usr/bin/env bash
find . | grep ".*\.txt" | xargs cat | tr A-Z a-z | tr -s ' ' '\n' | sort -n | uniq -c | sort -n | wc -l
