#!/usr/bin/env bash
find . -type f | grep ".txt" | wc -l | tr 'a-z' '0-9' | sort | uniq
