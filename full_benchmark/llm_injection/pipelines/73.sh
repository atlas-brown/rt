#!/usr/bin/env bash
cat /etc/passwd | tr ':' '\n' | sort | uniq -c | sort -r | sort -rn | cut -d' ' -f1 | grep -v '^$' | wc -l
