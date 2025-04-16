# Query: Count lines in each *.php file sorted by file in /testbed directory.

find /testbed -name '*.php' -type f | sort | xargs wc -l