# Query: Print the name and size of the 3 largest files in the directory /testbed/dir3

find /testbed/dir3 -type f -exec ls -lhS {} + 2>/dev/null | sort -rh -k5 | head -n 3