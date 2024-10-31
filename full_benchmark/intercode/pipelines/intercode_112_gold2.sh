# Query: Print the 3 largest directories in /workspace.

find /workspace -exec du -h {} + | sort -rh | head -n 3