#!/usr/bin/env bash
seq 1 100 | grep -v '^[0-9]*5$' | sort -n | sort | uniq -c | tr -s ' ' | cut -d' ' -f2 | wc -l
