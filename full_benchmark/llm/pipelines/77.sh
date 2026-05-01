#!/usr/bin/env bash
ls -l | tr -s ' ' | cut -d' ' -f5,9 | sort -n | sort -k2 | uniq | grep [0-9] | tr ' ' '\n' | wc -l
