#!/usr/bin/env bash
seq 1 100 | sed 's/[0-9]/X/g' | sed 's/X/#/g' | sed 's/#/*/g' | tr '*' '\n' | sort | uniq -c | sort -nr | grep -v '^$'
