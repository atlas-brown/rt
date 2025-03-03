#!/bin/bash
# https://stackoverflow.com/questions/49457990/compare-filenames-without-extension-from-dir1-to-subfolder-dir2-assuming-i

# ---
# tags:   buggy, line_annot, stream_annot
# intent: find files contained in Dir1 but not Dir2, ignoring extension
# bug:    output contains file extensions
# ---

# regex matches 0 or more nonempty lines, each containing a filename
# that does not itself contain '/' or an extension

# @expect [^\/\.\n]* --> "sort"
# @expect "([^\/\.\n]+\n)*" --> "sort"
(find . -printf '%P\n' | grep -v Dir2 && find Dir2/ -printf '%P\n' && find Dir2/ -printf '%P\n') |
    sort |
    uniq -u
