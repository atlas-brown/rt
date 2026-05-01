#!/usr/bin/env bash
cat data.txt | sed 's/[aeiou]/*/g' | grep "*" | sort -r | uniq | tr '*' 'X' | sort -n | wc -l
