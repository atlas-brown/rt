#!/bin/bash

# 4.1: find number of rounds
# @output " *[0-9]+"
cat $1 | tr ' ' '\n' | grep '\.' | wc -l
