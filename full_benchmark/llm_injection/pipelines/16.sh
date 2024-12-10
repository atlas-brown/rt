#!/usr/bin/env bash
find . -name "*.txt" | xargs cat | tr -d ' ' | cut -d' ' -f1 | sort | uniq -c | sort -nr | grep "[0-9]" | wc -l
