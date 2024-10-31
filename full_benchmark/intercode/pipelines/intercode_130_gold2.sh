# Query: List all files with their paths that have identical content in /workspace directory

find /workspace -type f -print0 | xargs -0 md5sum | sort | uniq -w32 -D