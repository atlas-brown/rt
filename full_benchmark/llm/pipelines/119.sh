#!/usr/bin/env bash
ls -l | sort -k5n | sort -k9 | cut -d' ' -f9 | tr '.' ' ' | sort -k2 | uniq | xargs grep .
