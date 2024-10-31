# Query: Counts all files in the /testbed folder and subfolders.

find /testbed -type f -exec ls -l {} \; | wc -l