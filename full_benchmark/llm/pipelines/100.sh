#!/usr/bin/env bash
ls -l | tr -d ' ' | cut -d' ' -f5 | sort -n | uniq | tr '\n' ',' | sed 's/,/, /g' | xargs find
