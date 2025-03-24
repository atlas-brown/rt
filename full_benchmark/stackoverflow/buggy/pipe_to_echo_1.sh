#!/bin/sh
# https://stackoverflow.com/questions/49541930/shell-script-to-hard-code-a-word-and-read-log-file

# ---
# tags: buggy, trivial
# bug:  piping to echo
# ---
# stream enable
tail -f |
    egrep -wi 'exception|critical' /var/log/cloudera-scm-server/cloudera- scm-server.log |
    echo "EDHDEV:ERROR" >> subash.txt
