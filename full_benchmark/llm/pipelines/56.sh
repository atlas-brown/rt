#!/usr/bin/env bash
find . -name "*.txt" | grep -v "txt" | grep "txt" | sort | uniq | tr '.' '_' | sed 's/_txt$//' | cut -d'/' -f2 | wc -l
