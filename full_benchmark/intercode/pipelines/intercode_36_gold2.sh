# Query: Display the 5 smallest files in the /testbed directory and its sub-directories ignoring any empty files.

find /testbed -type f -size +0c -exec du -b {} + | sort -rh | tail -n 5