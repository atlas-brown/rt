#!/usr/bin/env bash
################################################################################
# Commit message: Strip such lines starting with a #. Do not silently truncate lines if they have a # somewhere in between (like server=127.0.0.1#5353)  Signed-off-by: DL6ER <dl6er@dl6er.de>
# Commit URL: https://github.com/pi-hole/pi-hole/commit/36937b19132df631220e4a5912f889e58a357cbc
# Category: 
# Notes: 
# Changed content:
# - new_line=$(echo "${line}" | sed -e 's/#.*$//' -e '/^$/d')
# + new_line=$(echo "${line}" | sed -e 's/^\s*#.*$//' -e '/^$/d')
################################################################################
# output must not contain lines that are just comments
# output "~(\s*#.*)"
            new_line=$(echo "${line}" | sed -e 's/^\s*#.*$//' -e '/^$/d')