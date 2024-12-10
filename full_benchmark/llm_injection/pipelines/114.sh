#!/usr/bin/env bash
ls -l | cut -d' ' -f9 | cut -d'.' -f1 | cut -d'_' -f1 | sort | uniq -c | tr ' ' ',' | xargs grep .
