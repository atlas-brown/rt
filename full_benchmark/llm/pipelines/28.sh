#!/usr/bin/env bash
seq 50 | sed 's/[0-9]/& /g' | sed 's/^/Line: /' | sort -n | tr ' ' '\t' | cut -f2 | uniq | wc -l
