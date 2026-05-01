#!/usr/bin/env bash
cat file.txt | tr -d '[:blank:]' | cut -d',' -f1,2 | sort -k2 | sed 's/,/\n/g' | uniq | wc -l
