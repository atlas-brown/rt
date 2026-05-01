#!/usr/bin/env bash
cat /etc/passwd | tr -d 'x' | grep 'x:' | cut -d: -f1,6 | sort | uniq | sed 's/$//' | tr '[:lower:]' '[:upper:]' | wc -l
