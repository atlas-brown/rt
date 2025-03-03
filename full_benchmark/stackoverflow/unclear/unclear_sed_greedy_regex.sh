#!/bin/sh
# https://stackoverflow.com/questions/49611409/sed-replace-middle-number-pattern-surrounded-with-single-quotes

# ---
# tags:   bug, semantic_bug, sed, unclear
# intent: change a numeric value using sed
# bug:    '.*' in sed is greedy and user is not aware of it
# fix:    "s/max_value='[0-9.]*'/max_value='25'/g"
# ---

# input:
# <Init dflt_value='1.00' max_value='1000000.00' diff_ele='1.0' new='Yes' />

grep -rl 'max_value' | xargs sed -i "s/max_value='.*'/max_value='25'/g"
