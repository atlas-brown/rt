#!/bin/sh
# https://stackoverflow.com/questions/49565792/tail-f-search-file-with-match-and-latest-date-time

# ---
# tags: buggy, trivial
# bug:  piping output to ls
# ---

tail -f | ls -t /var/log/impala/impalad.demo.local.impala.log.INFO.* | head -1
