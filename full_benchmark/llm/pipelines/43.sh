#!/usr/bin/env bash
ls -R | tr -d ' ' | cut -d' ' -f1 | tr '[:upper:]' '[:lower:]' | sort | uniq -c | sort -nr | sed 's/^[ ]*//' | grep -v '^$' | wc -l
