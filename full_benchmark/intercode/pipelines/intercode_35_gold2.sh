# Query: Display the 5 largest files in the /testbed directory and its sub-directories.

find /testbed -type f -print0 | xargs -0 du -b | sort -rn | head -n 5