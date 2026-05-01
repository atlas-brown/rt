#!/usr/bin/env bash
ls -la | tr -s ' ' | tr ' ' '\n' | grep -v '^$' | tr -d ' ' | wc -l | xargs find . -name
