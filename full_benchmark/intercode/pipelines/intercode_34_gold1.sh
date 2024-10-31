# Query: Delete files in "/testbed/dir3/subdir1/subsubdir1/tmp" that are older than 2 days

find /testbed/dir3/subdir1/subsubdir1/tmp -type f -mtime +2 -print0 | xargs -0 rm -f