#!/bin/bash

# 9.2: extract the word BELL
# @assume "cat $1" --> "Be proud of your joB,\nEnjoy life's own talE;\nLive thinking of alL--\nLog out your emaiL!"
# @output "BELL"
cat $1 | cut -c 1-1 | tr -d '\n'
