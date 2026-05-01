#!/usr/bin/env bash
find . -type f -print0 | xargs -0 cat | sed 's/0x[0-9a-f]*/\n&\n/g' | sort -n | tr '\n' ' ' | uniq | wc -w
