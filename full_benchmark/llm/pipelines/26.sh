#!/usr/bin/env bash
find . -name "*.txt" | xargs cat | sed '/^$/d' | sort | grep "^[A-Z]" | tr A-Z a-z | uniq -c | wc -l
