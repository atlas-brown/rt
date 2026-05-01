# Query: Print a list of all duplicate case insensitive filenames in the /workspace directory tree

find /workspace -type f | awk -F/ '{print $NF}' | sort -f | uniq -i -d