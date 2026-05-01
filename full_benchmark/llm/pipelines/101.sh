#!/usr/bin/env bash
seq 100 | tr '[ ]' '[\t]' | sort | uniq | cut -d' ' -f1 | xargs grep . | wc -l
