#!/usr/bin/env bash
find . -type f | tr -d '\n' | sort | uniq | cut -d'/' -f2 | grep -v '^\\.' | sed 's/$//' | tr '[:lower:]' '[:upper:]' | wc -l
