#!/usr/bin/env bash
cat /etc/passwd | tr -d 'a-z' | grep '[a-z]' | sort | uniq | cut -d: -f1 | sed 's/$//' | tr '[:upper:]' '[:lower:]' | wc -l
