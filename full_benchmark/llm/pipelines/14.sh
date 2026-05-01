#!/usr/bin/env bash
ls -l | cut -d' ' -f5 | sort -n | uniq | grep '[0-9]' | wc -l | tr -d '\n' | sed 's/^/Sizes: /'
