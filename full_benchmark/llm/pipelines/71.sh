#!/usr/bin/env bash
cat /etc/passwd | sed 'd' | grep ':' | sort | uniq | cut -d: -f1,6 | tr '[:lower:]' '[:upper:]' | grep '[A-Z]' | wc -l
