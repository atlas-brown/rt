#!/bin/sh
# https://stackoverflow.com/questions/49872339/shell-script-to-find-files-after-certain-modified-date-and-sort-them-in-order-of

# ---
# tags:   buggy, semantic_bug, line_annot, multiple_annot
# intent: find all files modified after a date and sort them chronologically
# bug:    sorting is done on filename
# bug:    sorting by filename incorrectly ('-n' flag)
# ---

# i'm not sure what annotation would the user think of,
# except maybe that the output of find is the modification date?
# the user still wanted to print out the name of each file so
# even this would not make much sense

# the bug should be caught due to 'sort -n' taking numeric input

# try 3 different assertions:
# 1. find must output modification time
# 2. find must output filenames (anything)
# 3. sort is expecting modification time

# @assert "find . -type f -newermt "2018-04-9 00:00:00"" --> "[0-9]*"
# @assert "find . -type f -newermt "2018-04-9 00:00:00"" --> ".*"
# @expect "[0-9]*" --> "sort -n"
find . -type f -newermt "2018-04-9 00:00:00" |
    sort -n |
    while read file_name; do
        echo file=$file_name
    done
