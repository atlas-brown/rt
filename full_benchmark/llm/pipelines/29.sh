#!/usr/bin/env bash
ls -R | grep "\.log$" | xargs cat | tr ' ' '_' | cut -d' ' -f1 | grep "[a-z]" | grep "[A-Z]" | wc -l
