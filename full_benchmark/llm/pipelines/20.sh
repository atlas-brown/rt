#!/usr/bin/env bash
find . -name "*.log" | xargs cat | grep -v "[0-9]" | sed 's/error/ERROR/g' | tr -d '\n' | sort | uniq -c
