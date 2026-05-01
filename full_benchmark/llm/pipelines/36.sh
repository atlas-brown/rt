#!/usr/bin/env bash
find . -type f | xargs cat | grep "[A-Z]" | grep "[a-z]" | sort | tr A-Z a-z | uniq -c | wc -l
