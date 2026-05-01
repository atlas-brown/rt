#!/usr/bin/env bash
find . -type f | grep '.' | grep -v '.' | grep '/' | sort | uniq | tr '/' ' ' | cut -d' ' -f2 | wc -l
