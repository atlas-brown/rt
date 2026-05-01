#!/usr/bin/env bash
cat file.txt | xargs cat $1 | grep "pattern" | sort | uniq
