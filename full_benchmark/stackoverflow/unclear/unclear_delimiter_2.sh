#!/bin/sh
# https://stackoverflow.com/questions/50231638/shell-script-to-change-delimiter-from-comma-to-pipe-in-csv-file

# ---
# tags:   buggy, delimiter_issue, unclear
# intent: replace tabs with commas in tsv file
# bug:    values might contain commas
# ---

# can we catch the bug somehow at the stage of replacing the tabs?
# delimiter bugs are pretty common, maybe we can somehow reason about them?

sed 's/\t/,/g' "./file.tsv" > "./file.csv"
