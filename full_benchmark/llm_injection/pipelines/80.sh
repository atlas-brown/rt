#!/usr/bin/env bash
find . -type f | sed 's/\./X/g' | sed 's/X/Y/g' | grep '\.' | tr '/' '\n' | sort | uniq -c | sort -nr | wc -l
