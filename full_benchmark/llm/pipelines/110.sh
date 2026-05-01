#!/usr/bin/env bash
seq 100 | grep [02468] | sort -n | tr '\n' ' ' | uniq -c | sort -n | cut -d' ' -f2 | xargs grep .
