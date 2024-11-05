# Original: cat $1 | tr ' ' '\n' | grep '[A-Z]' | tr '[a-z]' '\n' | grep '[A-Z]' | tr -d '\n' | cut -c 1-4
# Error: The `cut` command is given an invalid combination of options. The `-c` option specifies character positions, while `-f` specifies fields. Using both together causes a type/format mismatch
cat $1 | tr ' ' '\n' | grep '[A-Z]' | tr '[a-z]' '\n' | grep '[A-Z]' | tr -d '\n' | cut -c 1-4 -f 2
