#!/usr/bin/env bash
seq 1 1000 | grep '^[0-9]*[02468]$' | grep '[13579]$' | sort -n | uniq -c | tr -s ' ' | cut -d' ' -f2 | wc -l
