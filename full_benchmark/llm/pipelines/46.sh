#!/usr/bin/env bash
cat /etc/passwd | tr -d ':' | tr ':' ' ' | cut -d: -f1,6 | sort | uniq | grep -v '^#' | sed 's/$//' | wc -l
