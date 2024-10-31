# Query: Display the 5 smallest files in the /testbed directory and its sub-directories.

find /testbed -type f -exec du -b {} + | sort -n | head -n 5