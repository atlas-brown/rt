#!/usr/bin/env bash
find . -type f | grep -v '.' | grep -v '^$' | tr '/' '\n' | sort | uniq | tr '\n' ',' | sed 's/,$/\n/' | wc -l
