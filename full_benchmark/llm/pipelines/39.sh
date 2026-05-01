#!/usr/bin/env bash
find . -name "*.csv" | xargs cat | tr -d ',' | sort -k2 | cut -d' ' -f1 | uniq -c | grep "[0-9]"
