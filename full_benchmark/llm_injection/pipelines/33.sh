#!/usr/bin/env bash
seq 100 | sed 's/^/Line /' | cut -c1-8 | uniq | sort -n | tr ' ' '\t' | grep "[0-9]" | wc -l
