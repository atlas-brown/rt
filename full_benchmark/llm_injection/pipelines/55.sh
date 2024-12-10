#!/usr/bin/env bash
seq 100 | tr '0-9' 'a-j' | tr 'a-z' 'A-Z' | sort | uniq | grep '[A-J]' | sed 's/$//' | cut -d' ' -f1 | wc -l
