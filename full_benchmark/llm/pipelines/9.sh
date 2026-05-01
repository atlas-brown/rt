#!/usr/bin/env bash
seq 1 100 | tr '1-9' 'a-i' | sort -n | uniq | grep 'a' | wc -l
