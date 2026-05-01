#!/usr/bin/env bash
grep "pattern" file.txt | wc -l | cut -f2
