#!/usr/bin/env bash
cat /etc/passwd | tr -d ':' | sed 's/:[^:]*$//g' | sort | uniq | grep -v '^$' | tr '/' '\n' | wc -l
