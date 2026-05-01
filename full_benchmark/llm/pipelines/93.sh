#!/usr/bin/env bash
ls -l | cut -d' ' -f9 | sort -n | tr '/' '\n' | sort | uniq -c | grep -v '^$' | cut -d' ' -f1 | wc -l
