#!/usr/bin/env bash
ls -l | tr -s ' ' | tr -d ' ' | cut -d' ' -f9 | sort | uniq | grep -v '^\\.' | sed 's/$//' | wc -l
