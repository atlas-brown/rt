#!/usr/bin/env bash
find . -type f | xargs cat | tr -d '[:punct:]' | sed 's/[0-9]/(&)/g' | grep "([0-9])" | sort | uniq -c
