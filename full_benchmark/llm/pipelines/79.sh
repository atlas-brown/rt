#!/usr/bin/env bash
cat /etc/passwd | cut -d: -f1,3 | tr ':' '\n' | sort | uniq -c | sort | grep -v '^$' | cut -d' ' -f1 | wc -l
