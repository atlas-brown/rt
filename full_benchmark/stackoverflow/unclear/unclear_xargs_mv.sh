#!/bin/sh
# https://stackoverflow.com/questions/50149281/error-when-transferring-huge-files-argument-list-too-long

# ---
# tags:   bug, semantic_bug, unclear
# intent: move a very large number of files to a directory
# bug:    'mv' is given its arguments even though its used by xargs,
#         'sm20180416*' gets expanded to a very long argument list,
#         which causes the error 'Argument list too long'
# issue:  'mv -f SOURCE... DIRECTORY' is valid, so it's not easy to detect
#         that the output of 'find' is unnecessary
# ---

# in this specific case, the fact that the third argument of 'mv'
# ends with a '/' might help spot the error

find ./ -name f | xargs mv -f sm20180416* /ora_arch/ssmfep_backup/
# fix: find ./ -name "sm20180416*" | xargs -I {} mv -f {} /ora_arch/ssmfep_backup/
