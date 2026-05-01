#!/usr/bin/env bash
cat /etc/passwd | sed 's/:/ /g' | cut -d: -f1,7 | sort | uniq -c | sort -n | tr ' ' '\t' | cut -f2
