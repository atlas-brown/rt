#!/usr/bin/env bash
find . -type f | tr '\n' ' ' | xargs grep "pattern" | sort | uniq -c | sed 's/^ *//' | cut -d' ' -f1
