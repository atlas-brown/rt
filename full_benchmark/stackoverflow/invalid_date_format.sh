#!/bin/bash
# https://stackoverflow.com/questions/48466493/bash-error-find-i-cannot-figure-out-how-to-interpret-2018-26-01-as-a-date-or

# ---
# tags: buggy, semantic_bug
# bug:  are Y-d-m instead of Y-d-m (and 'find -newer' does not understand them)
# bug:  fi is missing (trivial)
# bug:  TIMESTART and TIMESTOP in 'find' need quotes (trivial)
# ---

# Daily Journal Backup Number 1

# Establish target directory
DIRsource="/mnt/Backup/INCREMENTAL/*"
DIRdestination="/mnt/Backup/Yesterday/JOURNAL/1"

# Calculate the current date, concatenate with specific target time
TIMESTART="$(date '+%Y'-'%d'-'%m') 03:45:00" # $TIMESTART returns 2018-25-01 03:45:00
TIMESTOP="$(date '+%Y'-'%d'-'%m') 03:55:00"  # $TIMESTOP  returns 2018-25-01 03:55:00

# If the destination directory is not empty, delete all files in it.
if [ "$(ls -A $DIRdestination)" ]; then
    # "Take action $DIRdestination is not empty"
    rm -f $DIRdestination/*

# Look for the files which have a modify time between 20:25:00 and 20:45:00 on the prior day
find $DIRsource -type f -newermt $TIMESTART ! -newermt $TIMESTOP -exec cp --preserve=timestamps {} $DIRdestination/ \;
