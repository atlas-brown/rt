#!/bin/sh
# https://stackoverflow.com/questions/48393522/bash-script-to-delete-using-find

# ---
# tags: correct, line_annot, multiple_annot, complex_annot, awk
# ---

# @assert "find . -type f \( -iname "*.xml" \) -printf '%T@ %p\n'" --> "[0-9]+\.[0-9]+ .*\.xml"
# @assert "sort -rg" --> "[0-9]+\.[0-9]+ .*\.xml"
# @assert "sed -r 's/[^ ]* //'" --> ".*\.xml"
# @output "[a-zA-Z0-9.-]*\.xml"
# stream enable
find . -type f \( -iname "*.xml" \) -printf '%T@ %p\n' |
    sort -rg |
    sed -r 's/[^ ]* //' |
    awk '{w = $0; sub(".*/", "", w); sub("_[0-9_][0-9_]*.*", "", w);} !a[w]++'
