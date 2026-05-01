#!/usr/bin/env bash
find . -name "*.txt" | uniq | sort | tr '[/]' '[\t]' | cut -f2 | sort | uniq -c | xargs grep .
