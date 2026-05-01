# Query: Display the five biggest file sizes only in the /testbed directory

# @assume "find /testbed -type f -maxdepth 1 -exec du -b {} +" --> "([0-9]+[ \t]+[^\n]+\n)+"
find /testbed -type f -maxdepth 1 -exec du -b {} + | sort -rh | head -n 5
