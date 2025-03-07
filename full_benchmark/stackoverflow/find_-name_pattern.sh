#!/bin/sh
# https://stackoverflow.com/questions/50285704/how-to-ignore-or-exclude-backup-files-files-ending-with-in-shell-other-than

# ---
# tags:   correct, line_annot
# intent: calculate md5sum of files with names NOT ending with a '~'
# ---

# stream enable
# @assert "find /path/to/ -type f ! -name "*~" -print0" --> "(?!.*~)"
find /path/to/ -type f ! -name "*~" -print0 | xargs -0 md5sum
