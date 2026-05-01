#!/bin/bash

# 9.1: extract the word PORT
# @output "PORT"
# @file "${1}": "  most imPr1essive\n     me tO you!\n do letteRs middle\n= interneT's glue!"
cat $1 | tr ' ' '\n' | grep '[A-Z]' | tr '[a-z]' '\n' | grep '[A-Z]' | tr -d '\n' | cut -c 1-4
