#!/usr/bin/env bash
ls -l | tr -s ' ' | tr ' ' '_' | cut -d' ' -f5,9 | sort | uniq | tr '_' ' ' | xargs grep .
