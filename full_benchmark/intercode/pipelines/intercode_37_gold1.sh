# Query: Display the 5 smallest files in the /testbed directory and its sub-directories.

find /testbed -type f -exec ls -s {} \; | sort -n  | head -5