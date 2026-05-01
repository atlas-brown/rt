#!/usr/bin/env bash
cat /etc/passwd | tr -d ':' | cut -d: -f1,3,7 | sort | uniq | grep -v '^$' | tr '/' '\n' | wc -l
