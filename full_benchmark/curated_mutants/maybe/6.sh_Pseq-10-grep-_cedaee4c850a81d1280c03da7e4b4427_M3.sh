# @output "[0-9]+"
grep -oE "[0-9a-f]+" | head -n 5 | sort -n
