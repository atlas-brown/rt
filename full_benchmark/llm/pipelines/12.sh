#!/usr/bin/env bash
ls | tr 'a-z' 'A-Z' | grep ".sh" | sort | uniq | cut -d'.' -f1 | sed 's/^/File: /' | wc -l | xargs echo
