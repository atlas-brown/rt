#!/bin/bash
# https://stackoverflow.com/questions/50634717/how-do-i-get-grep-to-search-for-any-number-i-put-in-the-variable

# ---
# tags:   buggy, line_annot, stream_annot
# intent: find lines which contain either the string '2%' or the string '6%'
# bug:    array not dereferenced (returns only first value)
# ---

threshold=("2%" "6%") # are arrays in scope?

df -h > dffile

# @output "(.*(2%|6%).*)?"
# @output "^(.*(2%|6%).*\n)*$"
grep $threshold dffile >> thresh

# extract the 6th column of 'df -h', which contains mount points (paths)
cat thresh | awk '{print $6}' >> finding1

LINES=()
while IFS= read -r finding1; do
    find $finding1 -xdev -size +40M -exec ls -lah {} \; | head -n 10
done < "finding1"
