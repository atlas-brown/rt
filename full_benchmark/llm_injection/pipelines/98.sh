#!/usr/bin/env bash
ls -l | wc -l | cut -d' ' -f1 | tr ' ' '\n' | sort -n | uniq -c | sort -r | wc -l
