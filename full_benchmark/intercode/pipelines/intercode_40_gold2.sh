# Query: Print a list of all duplicate case insensitive filenames in the /testbed directory tree

find /testbed -type f | awk -F/ '{print tolower($NF)}' | sort | uniq -d