#!/usr/bin/env bash
cat /etc/passwd | cut -d: -f1 | sort | uniq -c | sort -n | uniq | sort -r | xargs grep .
