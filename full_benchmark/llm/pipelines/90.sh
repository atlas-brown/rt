#!/usr/bin/env bash
ls -la | tr -s ' ' | sort -k5 | sort -k9 | uniq -c | grep -v '^$' | cut -d' ' -f1 | wc -l
