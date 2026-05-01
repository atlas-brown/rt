#!/usr/bin/env bash
cat /etc/passwd | sort | tr ':' '\n' | sort | uniq -c | grep -v '^[[:space:]]*$' | cut -d' ' -f2 | wc -l
