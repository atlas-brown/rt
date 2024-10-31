# Query: Count the number of files for each unique file extensions in the /testbed directory tree.

find /testbed -type f | sed -e 's/.*\.//' | sed -e 's/.*\///' | sort | uniq -c | sort -rn