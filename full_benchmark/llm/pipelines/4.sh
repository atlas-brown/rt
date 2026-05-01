#!/usr/bin/env bash
cat file.txt | tr 'a-z' 'A-Z' | grep 'pattern'
