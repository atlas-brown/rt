# Query: Find the largest 2 directories under /workspace directory

find /workspace -type d -print0 | xargs -0 du | sort -n | tail -2