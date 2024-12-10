#!/usr/bin/env bash
ls -R | grep -v '^$' | sort | uniq | sort | uniq -c | sort -nr | uniq | cut -d' ' -f1 | wc -l
