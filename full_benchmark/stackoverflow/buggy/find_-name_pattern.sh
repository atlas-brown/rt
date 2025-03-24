#!/bin/sh
# https://stackoverflow.com/questions/50285704/how-to-ignore-or-exclude-backup-files-files-ending-with-in-shell-other-than

# ---
# tags:   correct, line_annot
# intent: calculate md5sum of files with names NOT ending with a '~'
# ---

# @expect ".+" --> "xargs -0 md5sum"
# @assert "find /path/to/ -type f -print0" --> "~(.*\~)"
# stream enable
find /path/to/ -type f -print0 | xargs -0 md5sum
