#!/usr/bin/env bash
ls -l | sed 'd' | grep '^-' | cut -d' ' -f9 | sort | uniq | tr '[:lower:]' '[:upper:]' | grep '[A-Z]' | wc -l
