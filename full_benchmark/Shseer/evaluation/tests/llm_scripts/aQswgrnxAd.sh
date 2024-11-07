
#!/bin/bash

# Define the directory and file extension
directory="/path/to/directory"
file_extension=".txt"

# Use the find command to locate all files with the specific file extension
find "$directory" -type f -name "*$file_extension" -exec rm {} \;
