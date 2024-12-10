#!/usr/bin/env bash
cat numbers.txt | sed 's/[0-9]/(&)/g' | tr -d '\n' | sort -n | tr ')(' '\n' | uniq | grep "[0-9]"
