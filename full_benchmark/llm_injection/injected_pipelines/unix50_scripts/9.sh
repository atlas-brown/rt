# Original: cat $1 | tr ' ' '\n' | grep 'x' | grep '\.' | cut -d '.' -f 2 | grep -v '[KQRBN]' | wc -l
# Error: The original pipeline counts lines, but changing `wc -l` to `wc -w` expects word counts, which doesn't match the single-character output from `grep -v '[KQRBN]'`. This causes a type/format mismatch.
cat $1 | tr ' ' '\n' | grep 'x' | grep '\.' | cut -d '.' -f 2 | grep -v '[KQRBN]' | wc -w
