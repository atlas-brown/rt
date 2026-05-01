#!/usr/bin/env bash
cat logs.txt | sed 's/.*ERROR://g' | cut -d' ' -f1 | sort -k2 | uniq | grep "[A-Z]" | wc -l
