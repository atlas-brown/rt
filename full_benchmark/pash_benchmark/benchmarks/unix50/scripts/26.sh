#!/bin/bash

# 9.4: four corners with E centered, for an "X" configuration
# @assume "cat $1" --> "\"S\"ay it with tec\"H\"\nThen answ\"E\"r the mail!\n(\"File\" plus this--)\n\"L\"et X cross this trai\"L\""
# @output "SHELL"
cat $1 | tr ' ' '\n' | grep "\"" | sed 4d | cut -d "\"" -f 2 | tr -d '\n'
