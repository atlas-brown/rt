#!/usr/bin/env bash
ls -l | tr -d ' ' | cut -d' ' -f9 | sort | uniq | grep -v '^\\.' | sed 's/$//' | tr '[:lower:]' '[:upper:]' | wc -l
