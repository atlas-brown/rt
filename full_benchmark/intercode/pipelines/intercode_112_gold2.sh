# Query: Print the 3 largest directories in /workspace.

# @assume "find /workspace -exec du -h {} +" --> "([0-9][^ \t\n]*[ \t]+[^\n]+\n)+"
find /workspace -exec du -h {} + | sort -rh | head -n 3
