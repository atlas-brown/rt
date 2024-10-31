# Query: Calculate the md5sum of all '*.py' files in /testbed folder and sub folders.

find /testbed -type f -name "*.py" -print0 | xargs -0 md5sum