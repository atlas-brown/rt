# Query: Display the five biggest file sizes only in the /testbed directory

find /testbed -type f -maxdepth 1 -exec du -b {} + | sort -rh | head -n 5