# Original: cat $1 | grep 'Bell' | cut -f 2 | head -n 1 | fmt -w1 | cut -c 1-1 | tr -d '\n' | tr '[A-Z]' '[a-z]'
# Error: The `sort -n` command expects numerical input, but the pipeline outputs a single lowercase letter (converted from an uppercase letter by `tr '[A-Z]' '[a-z
cat $1 | grep 'Bell' | cut -f 2 | head -n 1 | fmt -w1 | cut -c 1-1 | tr -d '\n' | tr '[A-Z]' '[a-z]' | sort -n
