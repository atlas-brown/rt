#!/usr/bin/env bash
seq 100 | grep -v [13579] | uniq -c | sort | tr -s '\t' | cut -d' ' -f2 | sort -n | xargs grep .
