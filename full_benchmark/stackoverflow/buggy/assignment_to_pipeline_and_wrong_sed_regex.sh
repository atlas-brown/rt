#!/bin/sh
# https://stackoverflow.com/questions/49658154/how-sed-command-used-in-shell-script

# ---
# tags: buggy, semantic_bug, line_annot, stream_annot, multiple_annot, sed
# bug:  variable assignment piped to sed
# bug:  sed regex is wrong
# note: heuristic of guaranteed empty output should be sufficient here, no annotations necessary?
# ---

# input:
# dummy statement Hello world 
# dummy 1 statement Hello Mike

file=commit.txt
while IFS= read line; do

    commitid=$line | sed "s/  HELLO.*'[^']*'/ /"
    # @var "$line": "dummy [0-9]+ statement Hello [a-zA-Z]+"
    # stream enable
    echo $line | sed "s/  HELLO.*'[^']*'/ /"
    echo $commitid
done < "$file"
