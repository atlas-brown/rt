#!/bin/sh
# https://stackoverflow.com/questions/50408319/how-to-omit-first-column-in-the-terminal-output-and-parallely-write-the-output

# ---
# tags: unclear
# ---

# no bugs in the code

./small_script.sh | while read R; do
    echo "$(date +%s) $R"
done |
    tee output.txt
