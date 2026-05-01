#!/usr/bin/env bash
ls -R | sort | uniq | grep -v '^$' | tr '[:upper:]' '[:lower:]' | sort | uniq | cut -d'.' -f1 | wc -l
