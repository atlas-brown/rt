# Query: Print a list of all duplicate case insensitive filenames in the /testbed directory tree

find /testbed -type f | awk -F/ '{print $NF}' | sort -f | uniq -i -d