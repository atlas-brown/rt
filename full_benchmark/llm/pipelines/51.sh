#!/usr/bin/env bash
seq 100 | sed 's/[0-9]//g' | sort -n | uniq | tr ' ' '\n' | grep . | cut -d' ' -f1 | wc -l | xargs find . -type f -name
