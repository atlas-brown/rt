#!/usr/bin/env bash
ls -la | tr -s ' ' | tr ' ' ',' | cut -d',' -f5 | sort -n | uniq | grep "[0-9]" | wc -l
