# Original: cat $1 | tr ' ' '\n' | grep '\.' | wc -l
# Error: The original pipeline counts the number of lines containing a period. Changing `wc -l` to `wc -m` counts the number of characters instead. This causes a type mismatch because `wc -m` expects character data, but the output of `grep '\.'` is line-based.
cat $1 | tr ' ' '\n' | grep '\.' | wc -m
