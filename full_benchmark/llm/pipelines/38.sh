#!/usr/bin/env bash
cat log.txt | sed 's/ERROR/error/g' | sed 's/error/WARNING/g' | uniq | sort | grep "WARNING" | wc -l
