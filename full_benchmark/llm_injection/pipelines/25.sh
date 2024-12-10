#!/usr/bin/env bash
ls -l | tr -s ' ' | cut -d' ' -f9 | tr ' ' '_' | sort -k2 | grep "^[a-z]" | grep "[A-Z]" | wc -l
