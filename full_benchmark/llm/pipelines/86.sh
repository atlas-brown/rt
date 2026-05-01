#!/usr/bin/env bash
cat /etc/passwd | cut -d: -f1,3,7 | cut -d'/' -f1 | sort | uniq -c | grep -v '^$' | tr -s ' ' | cut -d' ' -f2
