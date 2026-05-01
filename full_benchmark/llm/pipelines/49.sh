#!/usr/bin/env bash
seq 1000 | grep '[0-9]' | grep -v '[0-9]' | sort -n | tr '\n' ' ' | sed 's/ /\n/g' | uniq | cut -d' ' -f1 | wc -l
