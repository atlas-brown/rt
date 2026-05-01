#!/usr/bin/env bash
ls -l | tr -s ' ' | tr ' ' ',' | cut -d',' -f9 | sort -k2 | grep "[a-z]" | uniq -c | wc -l
