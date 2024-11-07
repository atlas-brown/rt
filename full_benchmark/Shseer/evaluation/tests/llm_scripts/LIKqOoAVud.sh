
#!/bin/bash

# Define the directory where we want to search for files
directory="/path/to/search"

# Use the find command to search for files in multiple subdirectories
find "$directory" -type f -name "*.txt" -exec sh -c 'mv "$0" "${0%.txt}_new.txt"' {} \;
