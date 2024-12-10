#!/usr/bin/env bash
find . -type f | tr '/' ' ' | sort | uniq | tr ' ' '/' | xargs find -name | sort | uniq -c
