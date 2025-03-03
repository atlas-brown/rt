#!/bin/sh
# https://stackoverflow.com/questions/49658154/how-sed-command-used-in-shell-script

# ---
# tags: buggy, semantic_bug, line_annot, stream_annot, multiple_annot, sed
# bug:  variable assignment piped to sed
# bug:  sed regex is wrong
# ---

# input:
# dummy statement Hello world 
# dummy 1 statement Hello Mike

file=commit.txt
while IFS= read line; do

    # @expect "dummy statement Hello world\ndummy 1 statement Hello Mike" --> "sed "s/  HELLO.*'[^']*'/ /""
    # @expect ".*Hello.*" --> "sed "s/  HELLO.*'[^']*'/ /""
    # @expect ".+" --> "sed "s/  HELLO.*'[^']*'/ /""
    commitid=$line | sed "s/  HELLO.*'[^']*'/ /"
    echo $commitid
done < "$file"
