# Query: Print a list of all duplicate case insensitive filenames in the /workspace directory tree

find /workspace -type f | awk -F/ '{print tolower($NF)}' | sort | uniq -d