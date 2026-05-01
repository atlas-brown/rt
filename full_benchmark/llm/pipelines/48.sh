#!/usr/bin/env bash
ls -l | tr -d '\n' | sort -k5,5n | cut -d' ' -f9 | grep . | uniq -c | sed 's/^[ ]*//' | tr ' ' '\t' | wc -l
