# Query: Display the 5 largest files in the /testbed directory and its sub-directories.

# @assume "find /testbed -type f -exec du -b {} +" --> "([0-9]+[ \t]+[^\n]+\n)+"
find /testbed -type f -exec du -b {} + | sort -rh | head -n 5
