#!/usr/bin/env bash
cat /etc/passwd | tr ' ' '\t' | cut -d' ' -f1 | sort | uniq | tr '\t' ' ' | xargs grep . | wc -l
