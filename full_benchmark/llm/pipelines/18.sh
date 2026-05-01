#!/usr/bin/env bash
find . -type f | xargs cat | sed 's/[0-9]//g' | sort | tr A-Z a-z | uniq | grep "[a-z]" | wc -l
