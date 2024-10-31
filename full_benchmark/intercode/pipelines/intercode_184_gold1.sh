# Query: Print the name and size of the 3 largest files in the directory /testbed/dir3

find /testbed/dir3 -type f -exec ls -lhS {} + | sort -rh -k5 | head -n 3