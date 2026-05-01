#!/usr/bin/env bash
seq 1000 | sort -n | uniq | sort -r | tr '0-9' 'a-j' | grep '[a-j]' | sed 's/$//' | cut -d' ' -f1 | wc -l
