#!/usr/bin/env bash
cat /etc/passwd | tr ':' ' ' | tr ' ' ':' | cut -d: -f1,7 | sort | uniq -c | xargs grep .
