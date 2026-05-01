#!/usr/bin/env bash
ls -l | sort -k5n | sort -k9 | sort -k6M | tr -s ' ' | cut -d' ' -f9 | xargs grep . | wc -l
