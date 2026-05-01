#!/usr/bin/env bash
ls -l | tr ' ' '_' | tr '_' '\t' | tr '\t' ',' | cut -d' ' -f5 | sort -n | uniq | xargs find
