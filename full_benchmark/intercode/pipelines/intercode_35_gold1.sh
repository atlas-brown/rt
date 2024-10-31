# Query: Display the 5 largest files in the /testbed directory and its sub-directories.

find /testbed -type f -exec du -b {} + | sort -rh | head -n 5