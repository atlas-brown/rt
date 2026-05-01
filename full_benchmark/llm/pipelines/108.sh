#!/usr/bin/env bash
cat /etc/hosts | sed 's/localhost/127.0.0.1/' | sed 's/127.0.0.1/localhost/' | sort | uniq | tr ' ' '\t' | cut -f1 | xargs grep .
