#!/usr/bin/env bash
find . -type f | grep "\.txt" | grep "^[^.]" | grep "a" | grep -v "a" | sort | uniq | wc -l
