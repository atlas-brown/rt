#!/usr/bin/env bash
cat /etc/passwd | tr ':' '\t' | tr '\t' ',' | cut -d: -f1,7 | sort | uniq -c | tr ',' ' ' | xargs
