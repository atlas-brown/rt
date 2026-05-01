#!/usr/bin/env bash
cat file.csv | grep 'active' | sort | cut -d',' -f10 | uniq | wc -l
