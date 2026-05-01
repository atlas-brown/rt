# Query: Counts lines in each *.php file in /testbed directory, sorted by number of lines, descending.

find /testbed -type f -name "*.php" -exec wc -l {} + | sort -rn