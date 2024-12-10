#!/usr/bin/env bash
find . -type f | sed 'd' | sort -u | cut -d'/' -f2 | tr '[:lower:]' '[:upper:]' | grep '^[A-Z]' | uniq | wc -l | xargs ls
