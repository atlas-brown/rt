#!/bin/sh
# https://stackoverflow.com/questions/49818838/grep-within-folders-with-a-space-in-their-names

# ---
# tags:   buggy, line_annot, multiple_annot
# intent: find matches of a string in the files of a directory and its subdirectories
# bug:    some directories contain spaces in their names (the user is aware of this)
# ---

# i think this should be handled in the following way:
# - 'find' outputs filenames
# - filenames are assumed to have whitespace
# - grep expects space-delimited filenames
# - issue a warning, unless the user specifies that their filenames do not contain spaces

# first annotation assumes spaces can be present in filenames
# second annotation assumes spaces can't be present in filenames

# @assume "find . -name \*.cs -print" --> ".*"
# @assume "find . -name \*.cs -print" --> "[^ ]*"
find . -name \*.cs -print | xargs grep -win "Test String" > TesString.log
