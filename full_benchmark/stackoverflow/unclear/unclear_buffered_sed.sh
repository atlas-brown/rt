#!/bin/sh
# https://stackoverflow.com/questions/48768359/tail-f-sed-to-file-doesnt-work

# ---
# tags: buggy, semantic_bug, sed, unclear
# bug:  sed buffers its data because its in the middle of a pipeline
#       and the user is not aware of this behavior
# fix:  sed -u/--unbuffered
# ---

# i don't think there's a way to know if the user expects the buffering or not

tail -f test.log | sed 's/a/b/' | tee -a a.txt
