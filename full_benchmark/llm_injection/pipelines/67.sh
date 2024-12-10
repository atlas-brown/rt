#!/usr/bin/env bash
ls -R | sed 'd' | sort -u | cut -d'.' -f1 | tr '[:lower:]' '[:upper:]' | grep '[A-Z]' | uniq | wc -l
