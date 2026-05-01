#!/usr/bin/env bash
cat /etc/passwd | sed 'd' | grep ':' | cut -d: -f1 | sort | uniq | tr '[:lower:]' '[:upper:]' | grep '[A-Z]' | wc -l
