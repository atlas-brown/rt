#!/usr/bin/env bash
seq 1 100 | tr '0-9' 'a-j' | tr 'a-j' '0-9' | sort -n | uniq -c | grep -v '^$' | cut -d' ' -f2 | wc -l
