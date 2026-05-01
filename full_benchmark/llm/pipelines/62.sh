#!/usr/bin/env bash
find . -type f | grep '.' | grep -v '.' | sort | uniq | tr '/' ' ' | cut -d' ' -f2 | sed 's/$//' | wc -l
