#!/usr/bin/env bash
seq 100 | tr -d ' ' | cut -d' ' -f1 | sort -n | uniq | tr '0-9' 'a-j' | grep '[a-j]' | sed 's/$//' | wc -l
