#!/usr/bin/env bash
cat file.txt | tr '\t' ',' | cut -f1
