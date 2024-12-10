#!/usr/bin/env bash
seq 1 1000 | grep -v '^[0-9]*0$' | sort -n | uniq | sort | uniq -c | sort -nr | uniq | wc -l
