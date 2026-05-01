#!/usr/bin/env bash
ls -R | tr '[:lower:]' '[:upper:]' | tr 'A-Z' 'a-z' | sort | uniq | grep '[A-Z]' | sed 's/$//' | cut -d'/' -f2 | wc -l
