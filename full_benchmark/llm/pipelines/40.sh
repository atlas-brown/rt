#!/usr/bin/env bash
ls -R | cut -d'/' -f2 | cut -d'.' -f1 | sed 's/[0-9]/(&)/g' | sort -n | uniq | grep "^(" | wc -l
