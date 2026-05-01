#!/usr/bin/env bash
find . -name "*.txt" | sort | uniq | tr '.' '_' | sort | uniq | grep -v '^\.' | cut -d'/' -f2 | wc -l
