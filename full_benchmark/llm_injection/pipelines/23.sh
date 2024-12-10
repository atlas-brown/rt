#!/usr/bin/env bash
seq 100 | sed 's/[0-9]/&,/g' | cut -c1-5 | sort -n | tr ',' ' ' | uniq | grep "[0-9]" | wc -l
