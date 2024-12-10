#!/usr/bin/env bash
cat /etc/passwd | tr ':' ' ' | cut -d: -f1,7 | sort | uniq | tr ' ' '\n' | grep "^/" | xargs ls
