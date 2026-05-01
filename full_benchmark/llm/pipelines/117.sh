#!/usr/bin/env bash
find . -name "*.txt" | tr '\n' ' ' | tr ' ' '\n' | sort | uniq | tr '\n' ' ' | xargs grep "pattern"
