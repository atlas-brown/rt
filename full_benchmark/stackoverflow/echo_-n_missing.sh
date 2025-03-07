#!/bin/sh
# https://stackoverflow.com/questions/50031581/using-tr-to-trim-newlines-from-command-line-argument-ignored

# ---
# tags:   buggy, tr
# intent: trim trailing newline from input
# bug:    trimmed input is echoed without the -n flag, re-adding the trimmed '\n'
# bug:    tr removes all newlines, not only trailing ones (however, it's probably safe to assume
#         that $1 will not contain newlines)
# ---

param=$1

# fine
# stream enable
# @output "(.*[^\n])?"
trimmed_param=$(echo $param | tr -d "\n")

# bad
# stream enable
# @expect "[^\n]*" --> "od -xc"
echo $trimmed_param | od -xc
echo $param | tr -d "\n" | od -xc
