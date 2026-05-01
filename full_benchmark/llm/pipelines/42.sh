#!/usr/bin/env bash
# @assume "xargs cat" --> ".* .*"
find . -type f | xargs cat | sed 's/[0-9]/#/g' | sed 's/#/*/g' | cut -d'|' -f1 | sort | uniq -c
