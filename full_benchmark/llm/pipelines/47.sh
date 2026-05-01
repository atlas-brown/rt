#!/usr/bin/env bash
find . -name "*.txt" | sort | sort -r | uniq | tr '.' '_' | sed 's/_txt$//' | grep -v '^\\.' | cut -d'/' -f2 | wc -l
