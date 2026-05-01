#!/usr/bin/env bash
ls -l | sed 's/ \+/ /g' | sed 's/\n//g' | tr ' ' '\n' | sort | uniq -c | grep -v '^$' | cut -d' ' -f1 | wc -l
