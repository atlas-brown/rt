#!/usr/bin/env bash
seq 100 | grep '[0-9]' | sort -n | uniq | tr '0-9' 'a-j' | grep '[k-z]' | wc -l | xargs find . -type f -name
