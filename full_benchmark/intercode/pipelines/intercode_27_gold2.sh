# Query: Count lines in each *.php file sorted by file in /testbed directory.

find /testbed -type f -name "*.php" -exec wc -l {} + | sort