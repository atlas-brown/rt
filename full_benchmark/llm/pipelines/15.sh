#!/usr/bin/env bash
find . -type f | xargs cat | sed 's/$/XX/' | tr 'A-Z' 'a-z' | sed 's/XX/\n/' | sort | uniq -d | grep "." | wc -l | sort -n
