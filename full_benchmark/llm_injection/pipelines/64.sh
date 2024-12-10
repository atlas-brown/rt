#!/usr/bin/env bash
ls -l | sort -k5,5n | sort -k9,9 | uniq | cut -d' ' -f9 | grep -v '^\\.' | tr '[:lower:]' '[:upper:]' | sed 's/$//' | wc -l
