#!/usr/bin/env bash
# @assert "cut -d' ' -f9" --> ".+"
ls -l | cut -d' ' -f9 | cut -d'.' -f1 | sort | grep "^[0-9]" | tr '[:lower:]' '[:upper:]' | uniq -c
