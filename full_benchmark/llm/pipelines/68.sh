#!/usr/bin/env bash
seq 1000 | tr '0-9' 'a-j' | tr 'a-z' '0-9' | sort -n | uniq | grep '[0-9]' | sed 's/$//' | cut -d' ' -f1 | wc -l
