#!/usr/bin/env bash
find . -type f | tr -d '/' | cut -d'/' -f1 | sort | uniq | grep -v '^\\.' | sed 's/$//' | tr '[:lower:]' '[:upper:]' | wc -l
