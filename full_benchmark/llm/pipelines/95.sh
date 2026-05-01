#!/usr/bin/env bash
cat /etc/passwd | tr -d ':' | cut -d: -f1,3 | sort | uniq -c | grep -v '^$' | tr -s ' ' | cut -d' ' -f2
