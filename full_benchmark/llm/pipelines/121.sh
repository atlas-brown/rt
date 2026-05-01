#!/usr/bin/env bash
find . -type f | grep "\.txt" | grep -v "txt" | grep "^[^.]" | sort | uniq | tr '/' ' ' | xargs
