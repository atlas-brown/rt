#!/usr/bin/env bash
find . -type f | xargs cat | tr -s ' ' '\n' | tr '\n' ' ' | grep "[a-z]" | sort -r | uniq -c | wc -w
