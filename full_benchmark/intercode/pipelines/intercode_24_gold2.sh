# Query: Count the number of files for each unique file extensions in the /testbed directory tree.

find /testbed -type f | awk -F. '{if (NF>1) print $NF}' | sort | uniq -c | sort -nr