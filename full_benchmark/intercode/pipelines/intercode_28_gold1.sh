# Query: Counts lines in each *.php file in /testbed directory, sorted by number of lines, descending.

find /testbed -name '*.php' -type f | xargs wc -l | sort -nr